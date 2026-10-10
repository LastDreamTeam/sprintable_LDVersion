// @vitest-environment node
import { describe, expect, it } from 'vitest';
import { resolveLocale, SUPPORTED_LOCALES } from './locale-negotiation';
describe('Simplified Chinese locale', () => {
  it('adds Chinese without removing English or Korean', () => {
    expect(SUPPORTED_LOCALES).toEqual(['en', 'ko', 'zh']);
  });
  it.each(['zh-CN,zh;q=0.9,en;q=0.8', 'zh-Hans-CN', 'ZH-cn'])('negotiates %s', (acceptLanguage) => {
    expect(resolveLocale({acceptLanguage})).toBe('zh');
  });
  it('honors explicit cookie and q weighting', () => {
    expect(resolveLocale({cookie:'zh',acceptLanguage:'en'})).toBe('zh');
    expect(resolveLocale({cookie:'en',acceptLanguage:'zh-CN'})).toBe('en');
    expect(resolveLocale({acceptLanguage:'zh;q=0,en;q=1'})).toBe('en');
    expect(resolveLocale({acceptLanguage:'en;q=0.1,zh;q=0.9'})).toBe('zh');
  });
});
