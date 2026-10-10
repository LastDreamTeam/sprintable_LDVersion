// @vitest-environment node
import { describe, expect, it } from 'vitest';
import { hasLocalMatch } from 'next/dist/shared/lib/match-local-pattern';
import config from '../../../next.config';

describe('LD native signed-local attachment optimization', () => {
  it('allows only the native attachment path to carry query parameters', () => {
    const patterns = config.images?.localPatterns;
    expect(hasLocalMatch(patterns, '/api/storage/local/bucket/org/image.png?exp=1&sig=abc')).toBe(true);
    expect(hasLocalMatch(patterns, '/logo.png')).toBe(true);
    expect(hasLocalMatch(patterns, '/api/auth/me?token=abc')).toBe(false);
    expect(hasLocalMatch(patterns, '/api/storage/local-other/file.png?sig=abc')).toBe(false);
    expect(hasLocalMatch(patterns, '/api/storage/local/../../../private.png?sig=abc')).toBe(false);
  });
  it('does not relax remote or private-network image access', () => {
    expect(config.images?.remotePatterns).toEqual([{ protocol: 'https', hostname: 'storage.googleapis.com' }]);
    expect(config.images?.dangerouslyAllowLocalIP).not.toBe(true);
    expect(config.images?.dangerouslyAllowSVG).not.toBe(true);
  });
});
