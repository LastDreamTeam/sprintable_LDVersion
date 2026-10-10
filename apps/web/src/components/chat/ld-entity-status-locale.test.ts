import { describe, expect, it } from 'vitest';
import { translateEntityStatus, renderEntityStatusLabel } from './entity-status-labels';

describe('LD selected-language entity status labels', () => {
  it.each(['zh', 'zh-CN', 'zh_Hans'])('%s renders a draft as Chinese', (locale) => {
    expect(translateEntityStatus('doc', 'draft', locale)).toBe('草稿');
    expect(renderEntityStatusLabel('doc', { kind: 'resolved', raw: 'draft' }, locale)).toBe('草稿');
    expect(renderEntityStatusLabel('doc', { kind: 'error' }, locale)).toBe('状态未知');
    expect(renderEntityStatusLabel('artifact', { kind: 'loading' }, locale)).toBe('无状态');
  });
  it('preserves native Korean, uses English fallback and never invents statuses', () => {
    expect(translateEntityStatus('doc', 'draft', 'ko')).toBe('초안');
    expect(translateEntityStatus('doc', 'draft', 'en')).toBe('Draft');
    expect(translateEntityStatus('doc', 'draft', 'fr')).toBe('Draft');
    expect(translateEntityStatus('doc', 'new-unknown', 'zh')).toBeNull();
    expect(translateEntityStatus('hypothesis', 'active', 'zh')).toBe('验证中');
    expect(translateEntityStatus('epic', 'active', 'zh')).toBe('进行中');
  });
});
