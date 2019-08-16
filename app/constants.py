FEMALE = 1
MALE = 2

GENDER = {
    FEMALE: 'female',
    MALE: 'male'
}

INACTIVE = 0
NEW = 1
ACTIVE = 2

REPORTER_STATUS = {
    INACTIVE: 'inactive',
    NEW: 'new',
    ACTIVE: 'active',
}

NOT_RECORDED = -1
NONE = 0
NONURGENT = 1
CRITICAL = 2

PATHOLOGIES = (NONURGENT, CRITICAL)

CONCLUSION = {
    NONE: ("No pathology",
           ("No gross pathology that would require clinical follow up "
            "has been identified")),
    NONURGENT: ("Non-urgent pathology",
                ("Pathology that requires non-urgent clinical follow"
                 " up has been identified")),
    CRITICAL: ("Critial pathology",
               ("Pathology that requires urgent clinical follow up "
                "has been identified. The individual should be "
                "referred for follow up immediately."))
}


LOW = 1
MEDIUM = 2
HIGH = 3

SESSION_PRIORITY = {
    LOW: "Low",
    MEDIUM: "High",
    HIGH: "Urgent"
}

MRI = 0
PET = 1

MODALITIES = {
    MRI: "MRI",
    PET: "PET"
}

# User roles
ADMIN_ROLE = 1
REPORTER_ROLE = 2

# Session data statuses
UNKNOWN = 0  # Unknown data status
PRESENT = 1  # Found matching session on MBI XNAT
NOT_FOUND = 2  # Did not find matching session on MBI-XNAT
NOT_SCANNED = 3  # This session was never scanned
INVALID_LABEL = 4  # The subject/visit labels need to be edited for this sess.
NOT_CHECKED = 5  # The data was not checked as it was already reported
UNIMELB_DARIS = 6  # The data was stored on Unimelb daris, no longer accessible
EXCLUDED = 7  # An executive decision was made to exclude this session
FIX_XNAT = 8  # It has been identified that the XNAT session needs to be fixed
FOUND_NO_CLINICAL = 9  # The session doesn't contain any clinical scans
NOT_REQUIRED = 10  # A report is not required

DATA_STATUS = {
    UNKNOWN: ("Unkown", "Unknown data status (run check_data_status method)"),
    PRESENT: ("Present", "Updated to match valid XNAT session"),
    NOT_FOUND: ("Not found in XNAT", "Found no matching session on XNAT"),
    NOT_SCANNED: ("Cancelled/interrupted", "Cancelled/interrupted/not-uploaded"
                  " session"),
    INVALID_LABEL: ("Invalid ID(s)", "Invalid ID(s) imported from FileMaker"),
    NOT_CHECKED: ("Not checked", "Already reported so not checked"),
    UNIMELB_DARIS: ("Unimelb DaRIS", "Stored in UniMelb DaRIS"),
    EXCLUDED: ("Excluded", "Executive decision to exclude"),
    FIX_XNAT: ("Fix in XNAT",
               "XNAT session needs to be renamed to match this"),
    FOUND_NO_CLINICAL: ("Found no clinical",
                        "No clinically relevant scans found in XNAT session"),
    NOT_REQUIRED: ("Not required",
                   "Report is not required (no clinically relevant scans "
                   "in project protocol)")
}

FIX_OPTIONS = [PRESENT, NOT_SCANNED, FIX_XNAT, NOT_REQUIRED, EXCLUDED]
