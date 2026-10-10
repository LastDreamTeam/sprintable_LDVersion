// @vitest-environment jsdom
import { act } from 'react';
import { createRoot, type Root } from 'react-dom/client';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { NextIntlClientProvider } from 'next-intl';
import { AgentProjectAccessSection } from './agent-project-access-section';
import { AccessMatrixTab } from '@/components/agents/access-matrix-tab';
import { ProjectAccessSection } from './project-access-section';
import en from '../../../messages/en.json';
import ko from '../../../messages/ko.json';
import zh from '../../../messages/zh.json';

(globalThis as { IS_REACT_ACT_ENVIRONMENT?: boolean }).IS_REACT_ACT_ENVIRONMENT = true;
let root: Root;
let container: HTMLDivElement;
beforeEach(() => {
  container = document.createElement('div'); document.body.append(container);
  root = createRoot(container);
});
afterEach(async () => {
  await act(async () => root.unmount()); container.remove(); vi.unstubAllGlobals();
});
async function flush() {
  await act(async () => { for (let i = 0; i < 8; i++) await Promise.resolve(); });
}
async function click(button: Element | null) {
  expect(button).not.toBeNull();
  await act(async () => (button as HTMLButtonElement).click()); await flush();
}
function dialogButton(label: string) {
  return [...document.querySelectorAll('[role="dialog"] button')].find((b) => b.textContent === label) ?? null;
}

describe.each([['en', en], ['ko', ko], ['zh', zh]] as const)('access confirmation in %s', (locale, messages) => {
  it.each(['detail', 'matrix', 'human'] as const)('%s requires confirmation; cancel is read-only', async (mode) => {
    const fetchMock = vi.fn(async (url: string, init?: RequestInit) => {
      let data: unknown = [];
      if (url.endsWith('/team-members?type=agent&include_inactive=true') || url.includes('/team-members?type=agent')) {
        data = [{ id: 'agent-1', name: 'Test agent', runtime_type: 'hermes' }];
      } else if (url === '/api/projects') data = [{ id: 'project-1', name: 'Test project' }];
      else if (url === '/api/agents/access-matrix') data = [{ agent_member_id: 'agent-1', project_id: 'project-1', record_id: 'grant-1' }];
      else if (url.endsWith('/access-candidates')) data = [{ id: 'human-1', user_id: 'user-1', name: 'Test member', role: 'member' }];
      else if (url.endsWith('/access')) data = [{ id: 'grant-1', member_id: 'agent-1', org_member_id: 'human-1', role: 'member' }];
      return { ok: true, status: init?.method === 'DELETE' ? 200 : 200, json: async () => ({ data }) };
    });
    vi.stubGlobal('fetch', fetchMock);
    await act(async () => root.render(
      <NextIntlClientProvider locale={locale} messages={messages} timeZone="UTC">
        {mode === 'detail' ? <AgentProjectAccessSection agentMemberId="agent-1" agentName="Test agent" projects={[{ id: 'project-1', name: 'Test project' }]} canEdit />
          : mode === 'matrix' ? <AccessMatrixTab /> : <ProjectAccessSection projectId="project-1" />}
      </NextIntlClientProvider>,
    ));
    await flush();
    const writes = () => fetchMock.mock.calls.filter(([, init]) => init?.method === 'DELETE');
    const toggle = () => mode === 'matrix'
      ? container.querySelector('button[aria-label="' + messages.agents.matrixCellGranted + '"]')
      : [...container.querySelectorAll('button')].find((b) => b.textContent === messages.settings.projectAccessAllowed) ?? null;
    await click(toggle());
    expect(writes()).toHaveLength(0);
    expect(document.querySelector('[role="dialog"]')?.textContent).toContain(messages.settings.ldAccessRevokeTitle);
    expect(document.querySelector('[role="dialog"]')?.textContent).toContain(mode === 'human' ? 'Test member' : 'Test agent');
    if (locale === 'zh') expect(document.querySelector('[role="dialog"]')?.textContent).not.toMatch(/[\uac00-\ud7af]/);
    await click(dialogButton(messages.common.cancel));
    expect(writes()).toHaveLength(0);
    await click(toggle());
    await click(dialogButton(messages.settings.ldAccessRevokeConfirm));
    expect(writes()).toHaveLength(1);
    expect(writes()[0][0]).toBe('/api/projects/project-1/access/grant-1');
  });
});
