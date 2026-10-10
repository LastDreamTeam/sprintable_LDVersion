'use client';

import { useEffect, useRef } from 'react';
import { useTranslations } from 'next-intl';
import { ConfirmDialog } from '@/components/ui/confirm-dialog';

export interface AccessRevokeTarget {
  recordId: string;
  name: string;
  project: string;
  agent: boolean;
}

/** LD: use the native dialog/design system. No API call until explicit confirmation. */
export function ProjectAccessRevokeDialog({ target, onCancel, onConfirm }: {
  target: AccessRevokeTarget | null;
  onCancel: () => void;
  onConfirm: () => void;
}) {
  const t = useTranslations('settings');
  const tc = useTranslations('common');
  const submitted = useRef(false);
  useEffect(() => { submitted.current = false; }, [target]);
  return (
    <ConfirmDialog
      open={target !== null}
      onOpenChange={(open) => { if (!open) onCancel(); }}
      title={t('ldAccessRevokeTitle')}
      description={target ? t(target.agent ? 'ldAgentAccessRevokeBody' : 'ldHumanAccessRevokeBody', {
        name: target.name, project: target.project,
      }) : ''}
      cancelLabel={tc('cancel')}
      confirmLabel={t('ldAccessRevokeConfirm')}
      onConfirm={() => {
        if (!target || submitted.current) return;
        submitted.current = true;
        onConfirm();
      }}
    />
  );
}
