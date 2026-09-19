# Frahoosh Web

نسخه Web/PWA فراهوش در همان مخزن نسخه Android قرار گرفت تا Web و Android از یک قرارداد مشترک Supabase و یک module catalog استفاده کنند.

## اجرا
این پوشه یک Web App است. فایل `runtime-config.js` باید با آدرس Supabase و anon key محیط واقعی ساخته شود؛ کلید service_role هرگز نباید در Web قرار گیرد.

## منبع مشترک
- `../shared/module_catalog.json`
- `../shared/frahoosh_contract.json`

مسیر داده زنده هر دو کلاینت Supabase است.