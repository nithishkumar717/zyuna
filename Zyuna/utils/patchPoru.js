const { Rest } = require('poru');

/**
 * Poru v5.3.0's Rest.prototype.get checks `content-type === "application/json"`,
 * which fails when Lavalink returns `application/json; charset=utf-8` and returns
 * a raw string instead of parsed JSON. This patch handles any JSON content-type.
 */
function patchPoruRest() {
    if (Rest.prototype.__zyunaPatched) return;
    Rest.prototype.__zyunaPatched = true;

    Rest.prototype.get = async function patchedGet(requestPath) {
        try {
            const req = await globalThis.fetch(this.url + requestPath, {
                method: 'GET',
                headers: this.headers
            });
            const contentType = (req.headers.get('content-type') || '').toLowerCase();
            const text = await req.text();
            if (!text) return null;

            const trimmed = text.trimStart();
            if (contentType.includes('application/json') || trimmed.startsWith('{') || trimmed.startsWith('[')) {
                try {
                    return JSON.parse(text);
                } catch {
                    return text;
                }
            }
            return text;
        } catch {
            return null;
        }
    };
}

module.exports = { patchPoruRest };
