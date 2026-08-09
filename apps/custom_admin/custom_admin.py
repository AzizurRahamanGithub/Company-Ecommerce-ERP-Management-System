from django.utils.translation import gettext_lazy as _
from django.templatetags.static import static


UNFOLD = {
    "DASHBOARD_TEMPLATE": "dashboard.html",
    "SITE_TITLE": "Admin Dashboard",
    "SITE_HEADER": "Administration",
    "SITE_URL": "",
    "SITE_SYMBOL": "admin_panel_settings",
    "LOGO": lambda request: static("images/logo.png"),
    "SHOW_HISTORY": True,
    "SHOW_VIEW_ON_SITE": True,
    "SHOW_SITE_HEADER": True,
    "FORMS": {
        "INLINE_ACTIONS": True,
    },
    "SITE_ICON": {
        "light": "https://amcconnect122125.s3.us-east-2.amazonaws.com/omkaars_logo.png",  # light mode
        "dark": "https://amcconnect122125.s3.us-east-2.amazonaws.com/omkaars_logo.png",  # dark mode
    },
    # "SITE_LOGO": lambda request: static("logo.svg"),  # both modes, optimise for 32px height
    "SITE_LOGO": {
        "light": "https://amcconnect122125.s3.us-east-2.amazonaws.com/omkaars_logo.png",  # light mode
        "dark": "https://amcconnect122125.s3.us-east-2.amazonaws.com/omkaars_logo.png",  # dark mode
    },
    "THEME": "dark",
    "ACTIONS": {
        "ENABLE_DELETE": True,
        "ENABLE_ADD": True,
        "ENABLE_CHANGE": True,
        "ENABLE_BULK_DELETE": True,
    },
    "ENVIRONMENT": "Development",
    "LOGIN": {
        "redirect_after": lambda request: "/admin/",
    },
    "STYLES": [
        lambda request: static("css/custom_admin.css"),
    ],
    "SCRIPTS": [
        lambda request: static("js/custom_admin.js"),
    ],
    "BORDER_RADIUS": "6px",
    "COLORS": {
        "primary": {
            "400": "oklch(0.7847 0.2074 235.03)",
            "500": "oklch(0.7847 0.2074 235.03)",
            "600": "oklch(0.7847 0.2074 235.03)",
            "700": "oklch(0.7847 0.2074 235.03)",
            "800": "oklch(0.7847 0.2074 235.03)",
            "900": "oklch(0.7847 0.2074 235.03)",
            "950": "oklch(0.7847 0.2074 235.03)",
            "300": "oklch(0.7847 0.2074 235.03)",
            "200": "oklch(0.7847 0.2074 235.03)",
            "100": "oklch(0.7847 0.2074 235.03)",
            "50": "oklch(0.7847 0.2074 235.03)",
        },
    },
    "EXTENSIONS": {
        "modeltranslation": {
            "flags": {"en": "🇺🇸", "bn": "🇧🇩"},
        },
    },
    "SIDEBAR": {
        "show_search": True,
        "show_all_applications": True,
        "navigation": [
        {
                
                "icon": "dashboard",
                "separator": True,
                "collapsible": False,
                "items": [
                    {
                        "title": "Dashboard ",
                        "icon": "dashboard",
                        "link": "/admin/custom_home/customdashboard/",
                    }
                ],
            },
            {
                "title": _("User Management"),
                "separator": True,
                "collapsible": True,
                "items": [
                    {
                        "title": _("Users"),
                        "icon": "verified_user",
                        "link": "/admin/auths/customuser/",
                    },
                    # {
                    #     "title": _("Admins"),
                    #     "icon": "verified_user",
                    #     "link": "/admin/auths/customuser/admins/",
                    # },
                    # {
                    #     "title": _("Staff Members"),
                    #     "icon": "supervisor_account",
                    #     "link": "/admin/auths/customuser/staff/",
                    # },
                    # {
                    #     "title": _("Regular Users"),
                    #     "icon": "person",
                    #     "link": "/admin/auths/customuser/users/",
                    # },
                    {
                        "title": _("Groups"),
                        "icon": "group",
                        "link": "/admin/auth/group/",
                    },
                ],
            },
            {
                "title": _("Deliveries"),
                "separator": True,
                "collapsible": True,
                "items": [
                    {
                        "title": _("Set Delivery Areas"),
                        "icon": "map",
                        "link": "/admin/customer/deliveryarea/",
                    },
                    {
                        "title": _("Set Delivery Cutoff Time"),
                        "icon": "schedule",
                        "link": "/admin/customer/deliverycustoff/",
                    }
                ],
            },
            {
                "title": _("Customer Management"),
                "separator": True,
                "collapsible": True,
                "items": [
                    {
                        "title": _("All Customers"),
                        "icon": "people",
                        "link": "/admin/customer/customer/",
                    }
                ]
            },
            {
                "title": _("Notifications"),
                "separator": True,
                "collapsible": True,
                "items": [
                    {
                        "title": _("All Notifications"),
                        "icon": "notifications",
                        "link": "/admin/notification/notification/",
                    },
                ],
            },
            # shop --------------------
            {
                "title": _("Products Management"),
                "separator": True,
                "collapsible": True,
                "items": [
                    {
                        "title": _("Products"),
                        "icon": "shopping_cart",
                        "link": "/admin/shop/products/",
                    },
                ],
            },
            {
                "title": _("Orders Management"),
                "separator": True,
                "collapsible": True,
                "items": [
                    {
                        "title": _("Orders"),
                        "icon": "shopping_cart",
                        "link": "/admin/order/order/",
                    },
                    {
                        "title": _("Order Items"),
                        "icon": "shopping_cart",
                        "link": "/admin/order/orderitem/",
                    },
                    {
                        "title": _("Payment History"),
                        "icon": "payment",
                        "link": "/admin/order/paymenthistory/",
                    },
                    {
                        "title": _("Invoices"),
                        "icon": "receipt",
                        "link": "/admin/order/invoice/",
                    },
                    {
                        "title": _("Delivery Notes"),
                        "icon": "receipt",
                        "link": "/admin/order/deliverynote/",
                    },
                ],
            },
            {
                "title": _("Job Category"),
                "separator": True,
                "collapsible": True,
                "items": [
                    {
                        "title": _("All Job Categories"),
                        "icon": "work",  # অথবা "category", "folder" ইত্যাদি
                        "link": "/admin/jobcategory/jobcategory/",
                    },
                ],
            },

                        
                        
                        {
                "title": _("Milk Management"),
                "separator": True,
                "collapsible": True,
                "items": [
                    {
                        "title": _("Milk Setup"),
                        "icon": "settings",  
                        "link": "/admin/milk_setup/milk_setup/"  
                    },
                    {
                        "title": _("Milk Quality"),
                        "icon": "book_online", 
                        "link": "/admin/milk_setup/milk_quality/"  
                    }
                ]
            },
            
            
            # -------------------- Equipment Management --------------------
        {
            "title": _("Equipment Management"),
            "separator": True,
            "collapsible": True,
            "items": [
                {
                    "title": "Equipment Cleaning",
                    "icon": "brush",
                    "link": "/admin/equipment/equipmentcleaning/"
                },
                {
                    "title": "Area Cleaning",
                    "icon": "layers",
                    "link": "/admin/equipment/areacleaning/",
                },
                # {
                #     "title": "Equipment Categories",
                #     "icon": "layers",
                #     "link": "/admin/equipment/equipmentcategory/",
                # },
            ],
        },

            
        ],
    },
    "TABS": [],
}
TINYMCE_DEFAULT_CONFIG = {
    "height": 420,
    "menubar": True,
    "plugins": "advlist autolink lists link image charmap preview anchor "
    "searchreplace visualblocks code fullscreen insertdatetime media "
    "table help wordcount",
    "toolbar": "undo redo | styles | bold italic underline | alignleft aligncenter alignright alignjustify | "
    "bullist numlist outdent indent | link image media | table | code | preview",
    "block_formats": "Paragraph=p; Heading 2=h2; Heading 3=h3",
    "content_style": "body {font-family: -apple-system, Segoe UI, Roboto, Arial, sans-serif;}",
    "branding": False,
}
SUMMERNOTE_CONFIG = {
    "iframe": True,  # use iframe mode
    "width": "100%",  # full width of admin container
    "height": "600px",  # taller editor
    "toolbar": [
        ["style", ["style", "bold", "italic", "underline", "strikethrough", "clear"]],
        ["font", ["fontsize", "fontname", "superscript", "subscript"]],
        ["color", ["color"]],
        ["para", ["ul", "ol", "paragraph", "height"]],
        ["table", ["table"]],
        ["view", ["fullscreen", "codeview", "help"]],
        ["history", ["undo", "redo"]],
    ],
    "popover": {
        "table": [
            ["add", ["addRowDown", "addRowUp", "addColLeft", "addColRight"]],
            ["delete", ["deleteRow", "deleteCol", "deleteTable"]],
        ],
        "air": [
            ["color", ["color"]],
            ["font", ["bold", "underline", "clear"]],
            ["para", ["ul", "paragraph"]],
        ],
    },
    "dialogsInBody": True,
    "disableDragAndDrop": False,
}
