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
    NONE: ("No pathology",
           ("No gross pathology that would require clinical follow up "
            "has been identified")),
    NONURGENT: ("Non-urgent pathology",
                ("pathology that requires non-urgent clinical follow"
                 " up has been identified")),
    CRITICAL: ("Critial pathology",
               ("pathology that requires urgent clinical follow up "
                "has been identified. The individual should be "
                "referred for follow up immediately."))
}


LOW = 0
MEDIUM = 1
HIGH = 2

SESSION_PRIORITY = {
    LOW: "Low",
    MEDIUM: "Medium",
    HIGH: "high"
}
