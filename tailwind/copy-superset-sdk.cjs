// Keep the browser SDK local and reproducible; no runtime CDN dependency.
const fs = require('node:fs');
const path = require('node:path');
const destination = path.join(__dirname, '../crm/static/crm/vendor/superset-embedded-sdk.js');
const source = fs.readFileSync(require.resolve('@superset-ui/embedded-sdk'), 'utf8');
fs.writeFileSync(destination, '/* @superset-ui/embedded-sdk 0.4.0; Apache-2.0. https://github.com/apache/superset */\n' + source);
