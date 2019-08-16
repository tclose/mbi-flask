import os.path as op
import xnatutils

dummy_file = '/tmp/dummy-dicom-file.dcm'

with open(dummy_file, 'w') as f:
    f.write('dummy-dicom-file-no-contents')

session_ids = [
    'MRH060_C03_MR02',
    'MRH017_100_MR01',
    'MRH017_200_MR01',
    'MRH007_005_MR01',
    'MRH000_029_MR01',
    'MRH000_025_MR01',
    'MRH000_089_MR01',
    'MRH017_001_MR01',
    'MRH032_002_MR02',
    'MRH000_202_MR01']


with xnatutils.connect('https://mbi-xnat.erc.monash.edu.au') as mbi_xnat:
    with xnatutils.connect(
            'https://mbi-xnat-dev.erc.monash.edu.au') as test_xnat:
        for sess_id in session_ids:
            mbi_session = mbi_xnat.experiments[sess_id]  # noqa pylint: disable=no-member
            test_project = test_xnat.projects[sess_id.split('_')[0]]  # noqa pylint: disable=no-member
            test_subject = test_xnat.classes.SubjectData(  # noqa pylint: disable=no-member
                label='_'.join(sess_id.split('_')[:-1]), parent=test_project)
            try:
                test_xnat.experiments[sess_id]  # noqa pylint: disable=no-member
            except KeyError:
                test_session = test_xnat.classes.MrSessionData(  # noqa pylint: disable=no-member
                    label=sess_id, parent=test_subject)
                # Loop through clinically relevant scans that haven't been
                # exported and export
                for mbi_scan in mbi_session.scans.values():
                    try:
                        test_scan = test_session.scans[mbi_scan.id]
                    except KeyError:
                        test_scan = test_xnat.classes.MrScanData(  # noqa pylint: disable=no-member
                            id=mbi_scan.id, type=mbi_scan.type,
                            parent=test_session)
                        resource = test_scan.create_resource('DICOM')
                        resource.upload(dummy_file, op.basename(dummy_file))

print('Done')
