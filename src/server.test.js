const request = require('supertest');
const app = require('../server');

describe('server routes', () => {
  test('GET /api/hello returns hello world payload', async () => {
    const res = await request(app).get('/api/hello');
    expect(res.status).toBe(200);
    expect(res.body).toEqual({
      message: 'Hello world from the Penn × Anthropic backend',
    });
  });
});
