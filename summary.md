# Diagnostics i18n Updates

## Summary

- Localized diagnostics panel UI: action group title, button labels, status strings, and metrics group titles now use i18n.t(...)
- Metrics mapping updated to use display_key->data_key and i18n.t for group titles
- Status display strings (CONNECTED/FAILED/ACTIVE/Normal) now localized
- Export button copied text now localized
- Added new i18n keys for English and Spanish in core/i18n.py: system_actions, restart_engine, force_safe_mode, gpu_vendor, ram_usage, cpu_usage, cache_status, label_units, resolved_mode, cache_config, cpu_load, copied
- Created diagnostics_i18n_keys.csv with new keys and translations
