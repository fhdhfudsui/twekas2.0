const express = require('express');
const fs = require('fs');
const app = express();
const PORT = process.env.PORT || 3000;

function loadKeys() {
  if (!fs.existsSync('keys.json')) return {};
  return JSON.parse(fs.readFileSync('keys.json', 'utf8'));
}

app.get('/verify', (req, res) => {
  const key = req.query.key;
  const keys = loadKeys();
  const data = keys[key];

  if (!data) {
    return res.json({ valid: false, reason: "Invalid key." });
  }
  if (data.banned) {
    return res.json({ valid: false, reason: "Key is banned." });
  }
  if (new Date(data.expires) <= new Date()) {
    return res.json({ valid: false, reason: "Key expired." });
  }

  res.json({
    valid: true,
    username: data.username,
    expires: data.expires,
    tier: data.tier
  });
});

app.listen(PORT, () => console.log(`Running on ${PORT}`));
