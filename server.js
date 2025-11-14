const express = require('express');
const cors = require('cors');

const app = express();
app.use(cors());
app.use(express.json());

// In-memory data to simulate a lightweight backend data store
const programInfo = {
  name: 'Penn × Anthropic Emp Matching Initiative',
  nextEvent: 'Kickoff fireside chat with Anthropic mentors',
  date: '2025-02-05T23:30:00.000Z',
  location: 'Tannenbaum Hall, Room 120',
};

const interestList = [];

app.get('/api/hello', (req, res) => {
  res.json({ message: 'Hello world from the Penn × Anthropic backend' });
});

app.get('/api/program', (req, res) => {
  res.json({
    ...programInfo,
    totalInterest: interestList.length,
  });
});

app.post('/api/interest', (req, res) => {
  const { name, email, focus } = req.body || {};
  if (!name || !email) {
    return res.status(400).json({ error: 'name and email are required' });
  }

  const entry = { name, email, focus: focus || 'general', timestamp: new Date().toISOString() };
  interestList.push(entry);

  return res.status(201).json({ message: 'Added to interest list', entry });
});

app.get('/api/interest', (req, res) => {
  res.json({ entries: interestList });
});

if (require.main === module) {
  const port = process.env.PORT || 5000;
  app.listen(port, () => {
    // eslint-disable-next-line no-console
    console.log(`Backend listening on http://localhost:${port}`);
  });
}

module.exports = app;
