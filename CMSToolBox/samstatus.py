"""
A module that checks the SAM status of a site

:authors: Max Goncharov <maxi@mit.edu> \n
          Daniel Abercrombie <dabercro@mit.edu>
"""

from .webtools import get_json

def is_sam_good(site, time_span=24, success=0.85):
    """
    Checks the SAM tests for success rate, and returns True if SAM tests were passing

    :param str site: Name of the site to check
    :param int time_span: Amount of time to check in hours
    :param float success: Fraction of success desired in timespan for site
    :returns: True if SAM tests are good, otherwise, False
    :rtype: bool
    """

    if (not site.startswith('T2_')) and (not site.startswith('T1_')):
        print " need valid site name"
        exit(0)

    time_span_str = 'last%s' % time_span
    gen_json =  get_json('wlcg-sam-cms.cern.ch', '/dashboard/request.py/latestresultssmry-json',
                        {'profile': 'CMS_CRITICAL_FULL',
                         'site': site}
                        )

    gen_probes = gen_json['data']['results'][0]['flavours']
    srm_host_name = ''
    ce_host_name = ''
    ce_flavour = ''
    for item in gen_probes:
        if item['servicename'] == 'SRM':
            srm_host_name = item['hosts'][0]['hostname']
        else:
            ce_host_name = item['hosts'][0]['hostname']
            ce_flavour = item['servicename']

    get_data = lambda flav, host: get_json('wlcg-sam-cms.cern.ch', '/dashboard/request.py/getTestResults',
                                           {'flavors': flav,
                                            'profile_name': 'CMS_CRITICAL_FULL',
                                            'hostname': host,
                                            'time_range': time_span_str}
                                           )

    def is_problem(success, data):
        """
        :param float success: the rate of success desired
        :param list data: Data from the WLCG SAM server
        :returns: True if the success rate of SAM test is below success
        :rtype: bool
        """
		# if success is less then 85% call it a problem
        items = 0
        bad = 0
        for item in data:
            stat = item[1]
            if stat == 'WHITE':
                continue

            items += 1
            if stat in ['CRITICAL', 'WARNING']:
                bad += 1

        return float(bad)/float(items) > (1.0 - success)

    for probe in get_data('SRM', srm_host_name)['data']:
        if is_problem(success, probe[1]):
            return False

    for probe in get_data(ce_flavour, ce_host_name)['data']:
        if 'WN-xrootd-access' not in probe[0]:
            continue
        if is_problem(success, probe[1]):
            return False

    return True
