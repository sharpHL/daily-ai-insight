/**
 * Cloudflare Worker for storing daily report feedback
 *
 * Setup:
 * 1. Create a KV namespace called "FEEDBACK"
 * 2. Bind it to this worker
 * 3. Deploy this worker
 *
 * API:
 * - POST /feedback - Save feedback
 * - GET /feedback?date=YYYY-MM-DD - Get feedback for a date
 * - GET /feedback/all - Get all feedback
 */

const CORS_HEADERS = {
  'Access-Control-Allow-Origin': '*',
  'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
  'Access-Control-Allow-Headers': 'Content-Type',
};

export default {
  async fetch(request, env, ctx) {
    // Handle CORS preflight
    if (request.method === 'OPTIONS') {
      return new Response(null, { headers: CORS_HEADERS });
    }

    const url = new URL(request.url);
    const path = url.pathname;

    try {
      // POST /feedback - Save feedback
      if (request.method === 'POST' && path === '/feedback') {
        const body = await request.json();
        const { date, items } = body;

        if (!date || !items) {
          return jsonResponse({ error: 'Missing date or items' }, 400);
        }

        // Get existing feedback for this date
        const existing = await env.FEEDBACK.get(`feedback:${date}`, 'json') || { items: [] };

        // Merge new feedback (newer overwrites older for same title)
        const itemMap = new Map();
        existing.items.forEach(item => itemMap.set(item.title, item));
        items.forEach(item => itemMap.set(item.title, item));

        const merged = {
          date,
          items: Array.from(itemMap.values()),
          updated_at: new Date().toISOString(),
        };

        // Save to KV
        await env.FEEDBACK.put(`feedback:${date}`, JSON.stringify(merged));

        // Also update the index of all dates
        const index = await env.FEEDBACK.get('feedback:index', 'json') || [];
        if (!index.includes(date)) {
          index.push(date);
          index.sort().reverse(); // Most recent first
          await env.FEEDBACK.put('feedback:index', JSON.stringify(index));
        }

        return jsonResponse({ success: true, count: merged.items.length });
      }

      // GET /feedback?date=YYYY-MM-DD - Get feedback for a date
      if (request.method === 'GET' && path === '/feedback') {
        const date = url.searchParams.get('date');

        if (date) {
          const feedback = await env.FEEDBACK.get(`feedback:${date}`, 'json');
          return jsonResponse(feedback || { date, items: [] });
        }

        // Return index if no date specified
        const index = await env.FEEDBACK.get('feedback:index', 'json') || [];
        return jsonResponse({ dates: index });
      }

      // GET /feedback/all - Get all feedback (for CI)
      if (request.method === 'GET' && path === '/feedback/all') {
        const index = await env.FEEDBACK.get('feedback:index', 'json') || [];
        const allFeedback = [];

        for (const date of index.slice(0, 30)) { // Last 30 days
          const feedback = await env.FEEDBACK.get(`feedback:${date}`, 'json');
          if (feedback) {
            allFeedback.push(feedback);
          }
        }

        return jsonResponse({ feedback: allFeedback });
      }

      // GET /health - Health check
      if (path === '/health') {
        return jsonResponse({ status: 'ok' });
      }

      return jsonResponse({ error: 'Not found' }, 404);

    } catch (error) {
      return jsonResponse({ error: error.message }, 500);
    }
  }
};

function jsonResponse(data, status = 200) {
  return new Response(JSON.stringify(data), {
    status,
    headers: {
      'Content-Type': 'application/json',
      ...CORS_HEADERS,
    },
  });
}
