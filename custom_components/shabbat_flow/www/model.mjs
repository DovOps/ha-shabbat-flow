export const DRAFT_KEY = 'shabbat-flow-draft-v1';
export const localeMetadata = { en: {direction: 'ltr'}, he: {direction: 'rtl'} };

export function parseDraft(raw) {
  if (!raw) throw new Error('no_draft');
  let value;
  try { value = JSON.parse(raw); } catch { throw new Error('bad_draft'); }
  if (!value || typeof value !== 'object' || Array.isArray(value) ||
      Object.keys(value).sort().join(',') !== 'config,plan' ||
      value.config?.schema_version !== 1 || value.plan?.schema_version !== 1 ||
      !localeMetadata[value.plan?.language]) throw new Error('bad_draft');
  return value; // Full schema + calendar validation is done by the compiler before loading.
}

export function translate(catalogs, language, key) {
  if (!Object.hasOwn(catalogs[language] ?? {}, key)) throw new Error(`Missing translation: ${language}/${key}`);
  return catalogs[language][key];
}

export function localTime(iso, language, timezone) {
  return new Intl.DateTimeFormat(language, {timeZone:timezone,month:'short',day:'numeric',hour:'2-digit',minute:'2-digit',hourCycle:'h23'}).format(new Date(iso));
}
