const yaml = require('js-yaml');
const fs = require('fs');
const path = require('path');

const baseDir = process.argv[2];
if (!baseDir) {
  console.error('Usage: node check_yaml.js <directory>');
  process.exit(1);
}

const results = { ok: [], failed: [] };

function checkDir(dir) {
  const entries = fs.readdirSync(dir, { withFileTypes: true });
  for (const entry of entries) {
    const fullPath = path.join(dir, entry.name);
    if (entry.isDirectory() && entry.name !== 'node_modules' && entry.name !== '.git') {
      checkDir(fullPath);
    } else if (entry.isFile() && /\.(yaml|yml)$/i.test(entry.name)) {
      try {
        const content = fs.readFileSync(fullPath, 'utf8');
        yaml.load(content);
        results.ok.push(fullPath);
      } catch (e) {
        results.failed.push({ file: fullPath, error: e.message });
      }
    }
  }
}

checkDir(baseDir);

if (results.failed.length > 0) {
  for (const f of results.failed) {
    console.error(`FAIL: ${f.file}`);
    console.error(`      ${f.error}`);
  }
  console.error(`\n${results.failed.length} file(s) failed, ${results.ok.length} passed`);
  process.exit(1);
} else {
  console.log(`All ${results.ok.length} YAML files passed`);
  process.exit(0);
}
