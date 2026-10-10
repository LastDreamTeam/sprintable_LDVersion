'use client';

import { Globe } from 'lucide-react';
import { useLocale } from 'next-intl';
import { isSupportedLocale } from '@/i18n/locale-negotiation';

const labels: Record<string, string> = {
  en: 'Interface language', ko: '화면 언어', zh: '界面语言',
};

export function LocaleSwitcher({ className = '' }: { className?: string }) {
  const locale = useLocale();
  return (
    <label className={`flex items-center gap-1 rounded-xl px-2 py-1.5 text-xs font-medium text-muted-foreground transition hover:bg-muted hover:text-foreground ${className}`.trim()}>
      <Globe className="h-3.5 w-3.5" aria-hidden="true" />
      <select
        aria-label={labels[locale] ?? labels.en}
        title={labels[locale] ?? labels.en}
        value={locale}
        className="min-w-0 cursor-pointer rounded bg-background text-foreground outline-offset-2"
        onChange={(event) => {
          const next = event.target.value;
          if (!isSupportedLocale(next)) return;
          document.cookie = `locale=${next};path=/;max-age=31536000;SameSite=Lax${location.protocol === 'https:' ? ';Secure' : ''}`;
          window.location.reload();
        }}
      >
        <option value="zh">简体中文</option>
        <option value="en">English</option>
        <option value="ko">한국어</option>
      </select>
    </label>
  );
}
