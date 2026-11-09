// IBM watsonx.ai Granite Service
// Handles all AI interactions: NLP query understanding, book recommendations, summarization
// Uses ibm/granite-4-h-small via textChat API (IBM Cloud Lite)

const { WatsonXAI } = require('@ibm-cloud/watsonx-ai');
const { IamAuthenticator } = require('ibm-cloud-sdk-core');

let watsonxClient = null;

/**
 * Initialize the IBM watsonx.ai client (lazy singleton)
 */
function getWatsonxClient() {
  if (!watsonxClient) {
    if (!process.env.WATSONX_API_KEY || !process.env.WATSONX_PROJECT_ID) {
      throw new Error('IBM watsonx.ai credentials not configured. Set WATSONX_API_KEY and WATSONX_PROJECT_ID in .env');
    }
    watsonxClient = WatsonXAI.newInstance({
      version: '2024-05-31',
      serviceUrl: process.env.WATSONX_URL || 'https://us-south.ml.cloud.ibm.com',
      authenticator: new IamAuthenticator({
        apikey: process.env.WATSONX_API_KEY,
      }),
    });
  }
  return watsonxClient;
}

const MODEL_ID = process.env.GRANITE_MODEL_ID || 'ibm/granite-4-h-small';

/**
 * Call IBM Granite via textChat API (instruct / chat mode)
 * @param {string} systemPrompt
 * @param {string} userPrompt
 * @param {object} options
 * @returns {Promise<string>}
 */
async function chatWithGranite(systemPrompt, userPrompt, options = {}) {
  const client = getWatsonxClient();

  const response = await client.textChat({
    modelId: MODEL_ID,
    projectId: process.env.WATSONX_PROJECT_ID,
    messages: [
      { role: 'system', content: systemPrompt },
      { role: 'user', content: userPrompt },
    ],
    maxTokens: options.maxTokens || 512,
    temperature: options.temperature || 0.7,
  });

  const text = response.result?.choices?.[0]?.message?.content || '';
  return text.trim();
}

/**
 * Understand a student's natural language query and extract intent + keywords
 */
async function understandQuery(query, studentProfile = {}) {
  const systemPrompt = `You are a Library AI Assistant. Analyze the student query and extract structured information.
Respond ONLY with valid JSON — no explanation, no markdown fences.`;

  const contextLines = [];
  if (studentProfile.major) contextLines.push(`Student major: ${studentProfile.major}`);
  if (studentProfile.year) contextLines.push(`Academic year: Year ${studentProfile.year}`);
  if (studentProfile.currentCourses?.length) contextLines.push(`Current courses: ${studentProfile.currentCourses.join(', ')}`);

  const userPrompt = `Student query: "${query}"
${contextLines.join('\n')}

Return ONLY this JSON (fill every field):
{
  "intent": "one of: search_book | get_recommendation | check_availability | reserve_book | join_waitlist | get_syllabus_books | general_help",
  "keywords": ["key", "search", "terms"],
  "subject": "main subject or topic",
  "bookTitle": "specific book title if mentioned, else null",
  "author": "specific author if mentioned, else null",
  "course": "specific course if mentioned, else null",
  "level": "beginner or intermediate or advanced or null",
  "summary": "one sentence description of what the student needs"
}`;

  try {
    const text = await chatWithGranite(systemPrompt, userPrompt, { maxTokens: 300, temperature: 0.1 });
    // Extract JSON from response (in case model wraps it)
    const jsonMatch = text.match(/\{[\s\S]*\}/);
    if (jsonMatch) {
      const parsed = JSON.parse(jsonMatch[0]);
      // Normalise intent
      const validIntents = ['search_book', 'get_recommendation', 'check_availability', 'reserve_book', 'join_waitlist', 'get_syllabus_books', 'general_help'];
      if (!validIntents.includes(parsed.intent)) parsed.intent = 'search_book';
      return parsed;
    }
    throw new Error('No JSON found in response');
  } catch (err) {
    console.error('Granite NLP error:', err.message);
    // Fallback: basic keyword extraction
    return {
      intent: 'search_book',
      keywords: query.toLowerCase().split(/\s+/).filter(w => w.length > 3),
      subject: query,
      bookTitle: null,
      author: null,
      course: null,
      level: null,
      summary: query,
    };
  }
}

/**
 * Generate personalized book recommendations using IBM Granite
 */
async function generateRecommendations(studentProfile, availableBooks, queryContext = '') {
  const bookList = availableBooks.slice(0, 20).map(b =>
    `- "${b.title}" by ${b.author} [${b.subject}] (Available: ${b.availableCopies > 0 ? 'Yes' : 'No'})`
  ).join('\n');

  const systemPrompt = `You are an expert academic librarian AI. Recommend the most suitable books for this student.
Be specific, helpful, and concise. Format your response clearly with numbered recommendations.`;

  const userPrompt = `Student Profile:
- Name: ${studentProfile.name}
- Major: ${studentProfile.major}
- Year: Year ${studentProfile.year}
- Current courses: ${studentProfile.currentCourses?.join(', ') || 'Not specified'}
- Study interests: ${studentProfile.interests?.join(', ') || 'Not specified'}
${queryContext ? `- Specific request: ${queryContext}` : ''}

Available books in library:
${bookList}

Provide 3-5 personalized book recommendations with brief reasons why each book suits this student.`;

  try {
    return await chatWithGranite(systemPrompt, userPrompt, { maxTokens: 600, temperature: 0.6 });
  } catch (err) {
    console.error('Granite recommendation error:', err.message);
    return 'I apologize, but I am unable to generate personalized recommendations at the moment. Please browse our catalog or speak with a librarian.';
  }
}

/**
 * Generate a friendly AI response to a student's general library question
 */
async function generateAgentResponse(userMessage, context = {}) {
  const systemPrompt = `You are a friendly, knowledgeable Library AI Agent at a university library.
You help students find books, check availability, make reservations, and get academic recommendations.
Be concise, helpful, and encouraging. Keep responses under 150 words.`;

  const contextStr = Object.entries(context)
    .filter(([, v]) => v)
    .map(([k, v]) => `${k}: ${v}`)
    .join('\n');

  const userPrompt = contextStr ? `${contextStr}\n\nStudent: ${userMessage}` : userMessage;

  try {
    return await chatWithGranite(systemPrompt, userPrompt, { maxTokens: 250, temperature: 0.7 });
  } catch (err) {
    console.error('Granite agent response error:', err.message);
    return "I'm here to help you find the perfect learning resources! Could you tell me more about what you're looking for — a specific book, subject, or course material?";
  }
}

/**
 * Analyze a course syllabus text and extract required/recommended books
 */
async function analyzeSyllabus(syllabusText) {
  const systemPrompt = `You are a Library AI that extracts book references from course syllabi.
Respond ONLY with valid JSON — no markdown fences, no extra text.`;

  const userPrompt = `Extract all book references from this syllabus text and return ONLY this JSON:
{
  "required": [{"title": "...", "author": "...", "isbn": "..." }],
  "recommended": [{"title": "...", "author": "...", "isbn": "..."}],
  "topics": ["topic1", "topic2"]
}

Syllabus text:
${syllabusText.substring(0, 2000)}`;

  try {
    const text = await chatWithGranite(systemPrompt, userPrompt, { maxTokens: 400, temperature: 0.1 });
    const jsonMatch = text.match(/\{[\s\S]*\}/);
    if (jsonMatch) return JSON.parse(jsonMatch[0]);
    return { required: [], recommended: [], topics: [] };
  } catch (err) {
    console.error('Granite syllabus analysis error:', err.message);
    return { required: [], recommended: [], topics: [] };
  }
}

module.exports = {
  chatWithGranite,
  understandQuery,
  generateRecommendations,
  generateAgentResponse,
  analyzeSyllabus,
};
