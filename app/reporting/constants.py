INACTIVE = 0
NEW = 1
ACTIVE = 2

REPORTER_STATUS = {
    INACTIVE: 'inactive',
    NEW: 'new',
    ACTIVE: 'active',
}

NONE = 0
NONURGENT = 1
CRITICAL = 2

CONCLUSION = {
    NONE: ("No PATH",
           ("No gross PATH that would require clinical follow up "
            "has been identified")),
    NONURGENT: ("Non-urgent PATH",
                ("PATH that requires non-urgent clinical follow"
                 " up has been identified")),
    CRITICAL: ("Critial PATH",
               ("PATH that requires urgent clinical follow up "
                "has been identified. The individual should be "
                "referred for follow up immediately."))
}
