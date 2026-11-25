{
    "name": "Thai Localization - Buddhist Era Year",
    "version": "18.0.1.0.15",
    "summary": "Display dates and datetimes with Buddhist Era years for Thailand.",
    "category": "Localization/Thailand",
    "author": "Sansiri Tanachutiwat, Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/l10n-thailand",
    "license": "AGPL-3",
    "depends": ["web", "base_setup"],
    "data": [
        "views/res_config_settings_views.xml",
        "views/res_users_views.xml",
    ],
    "assets": {
        "web.assets_backend": [
            "l10n_th_year_be/static/src/js/date_be_field.esm.js",
        ],
    },
    "installable": True,
    "application": False,
    "development_status": "Beta",
    "maintainers": ["sansirit"],
}
