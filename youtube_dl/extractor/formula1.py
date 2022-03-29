# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor
from ..utils import str_or_none


class Formula1IE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?formula1\.com/en/latest/video\.[^.]+\.(?P<id>\d+)\.html'
    _TEST = {
        'url': 'https://www.formula1.com/en/latest/video.race-highlights-spain-2016.6060988138001.html',
        'md5': 'be7d3a8c2f804eb2ab2aa5d941c359f8',
        'info_dict': {
            'id': '6060988138001',
            'ext': 'mp4',
            'title': 'Race highlights - Spain 2016',
            'timestamp': 1463332814,
            'upload_date': '20160515',
            'uploader_id': '6057949432001',
        },
        'add_ie': ['BrightcoveNew'],
    }
    BRIGHTCOVE_URL_TEMPLATE = 'http://players.brightcove.net/6057949432001/S1WMrhjlh_default/index.html?videoId=%s'

    def _real_extract(self, url):
        bc_id = self._match_id(url)
        return self.url_result(
            self.BRIGHTCOVE_URL_TEMPLATE % bc_id, 'BrightcoveNew', bc_id)


class F1TVIE(InfoExtractor):
    _VALID_URL = r'https?://f1tv\.formula1\.com/detail/(?P<id>\d+)/(?:[\w-]+)'

    _TESTS = [{
        'url': 'https://f1tv.formula1.com/detail/1000000748/2019-singapore-grand-prix',
        'skip': 'Requires subscription'
    }, {
        'url': 'https://f1tv.formula1.com/detail/1000002299/2017-australian-grand-prix',
        'skip': 'Requires subscription'
    }, {
        'url': 'https://f1tv.formula1.com/detail/1000002895/1987-british-grand-prix',
        'skip': 'Requires subscription'
    }]

    _API_BASE_VID = 'https://f1tv.formula1.com/2.0/R/ENG/WEB_HLS/ALL'
    _API_BASE_META = 'https://f1tv.formula1.com/3.0/R/ENG/WEB_DASH/ALL/CONTENT/VIDEO/{0}/F1_TV_Pro_Monthly/2?contentId={0}'

    # Extract formats from a perspective's m3u8 stream
    def get_formats(self, contentId, url, title):
        stream_url = self._API_BASE_VID + '/' + url

        # Tracker, Data and Driver cams all have copies of commentary audio
        # Only International and F1 Live/PLC have unique commentary
        is_audio_unique = title == 'INTERNATIONAL' \
            or title == 'F1 LIVE' \
            or title == 'PIT LANE'

        stream_json = self._download_json(stream_url, contentId)
        m3u8_url = stream_json['resultObj']['url']

        m3u8 = self._extract_m3u8_formats(m3u8_url,
                                          contentId,
                                          'mp4',
                                          'm3u8_native',
                                          m3u8_id=title)

        stream_formats = []

        for s_format in m3u8:
            is_teamradio = s_format['format_id'].endswith('Team Radio')

            # Skip copies of commentary audio
            if s_format['vcodec'] == 'none' \
               and not (is_audio_unique or is_teamradio):
                continue

            # Make the format names more predictable. By default, video
            # qualities are differentiated by file size, not resolution
            name, _ = s_format['format_id'].split('-', 1)
            res = ''
            if 'height' in s_format:
                res = str_or_none(s_format['height']) + 'p'
            lang = ''
            if 'language' in s_format:
                lang = 'audio-' + s_format['language']
            s_format['format_id'] = '{}-{}{}'.format(name, res, lang)
            stream_formats.append(s_format)

        return stream_formats

    def _real_extract(self, url):
        contentId = self._match_id(url)
        contentInfo = self._download_json(self._API_BASE_META.format(contentId),
                                          contentId)
        metadata = contentInfo['resultObj']['containers'][0]['metadata']
        event_title = metadata['title']

        formats = []

        # Contains all m3u8's for all streams including all driver cams
        if 'additionalStreams' in metadata:
            for stream in metadata['additionalStreams']:
                formats += self.get_formats(contentId,
                                            stream['playbackUrl'],
                                            stream['title'])
        else:
            # Races 2017 and before only have one stream
            formats += self.get_formats(contentId,
                                        'CONTENT/PLAY?contentId=' + contentId,
                                        'INTERNATIONAL')

        return {
            'id': contentId,
            'title': event_title,
            'formats': formats,
        }
