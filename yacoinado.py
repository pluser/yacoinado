#!/usr/bin/env python
# -*- coding: utf-8 -*- #

# Copyright (c) 2015, Kaoru Esashika
# All rights reserved.

# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:

# * Redistributions of source code must retain the above copyright notice, this
#   list of conditions and the following disclaimer.

# * Redistributions in binary form must reproduce the above copyright notice,
#   this list of conditions and the following disclaimer in the documentation
#   and/or other materials provided with the distribution.

# * Neither the name of yacoinado nor the names of its
#   contributors may be used to endorse or promote products derived from
#   this software without specific prior written permission.

# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE
# FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
# DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
# SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
# CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
# OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
# OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.


import sys
import os
import re
import hashlib
import argparse
import requests
import bencodepy


COINADO_SECRET = os.getenv('YACOINADO_SECRET')
if not COINADO_SECRET:
	print('Please set YACOINADO_SECRET environment variable', file=sys.stderr)
	sys.exit()


def get_torrent_file(url):
	response = requests.get(url)
	return response.content


def get_hash(binary):
	decoded_data = bencodepy.decode(binary)
	decoded_info = decoded_data[b'info']
	encoded_info = bencodepy.encode(decoded_info)
	torrent_hash = hashlib.sha1(encoded_info).hexdigest()
	return torrent_hash


def get_endpoint(torrent_hash, select=None):
	if select:
		import urllib.parse
		quoted = urllib.parse.quote(select)
		# quoted = re.sub(r'[^ \t\n\r\f\va-zA-Z0-9_\[\]\(\).,\'\"]+', '_', select)
		endpoint = 'https://coinado.io/i/{}/search/{}?u={}'.format(torrent_hash, quoted, COINADO_SECRET)
	else:
		endpoint = 'https://coinado.io/i/{}/auto?u={}'.format(torrent_hash, COINADO_SECRET)
	return endpoint


def get_filelist(torrent_hash):
	import bs4
	response = requests.get('http://btdigg.org/search?info_hash={}'.format(torrent_hash))
	html = bs4.BeautifulSoup(response.text, 'html.parser')
	filename = list()
	for entry in html.find('th', text='File size').parent.next_siblings:
		filename.append(entry.contents[1].text)
	return filename


def get_payload(torrent_hash, dest_path, select=None, permit_overwrite=False):
	def spinning_cursor():
		while True:
			for cursor in r'|/-\\':
				yield cursor
	spinner = spinning_cursor()

	def display_progress(count, size, total):
		percentage = count * size / total
		sys.stdout.write(
			'\r{} {:.3%} ({:,}/{:,} bytes) downloaded.'
			.format(next(spinner), percentage, count * size, total))
		sys.stdout.flush()

	endpoint = get_endpoint(torrent_hash, select)
	print('Connecting...')
	response = requests.get(endpoint, stream=True)
	if os.path.isdir(dest_path):
		match = re.search(r'''filename=['"](.*?)['"]''', response.headers['Content-Disposition'])
		filename = match.group(1)
		path = os.path.join(os.path.abspath(dest_path), filename)
	elif os.path.isfile(dest_path):
		if permit_overwrite:
			path = os.path.abspath(dest_path)
		else:
			print('file: {} exists.'.format(dest_path), file=sys.stderr)
			print('To overwrite the file, please add --force option', file=sys.stderr)
			return
	else:
		path = os.path.abspath(dest_path)

	with open(path, mode='wb') as fd:
		print('Connected.')
		print('Destination: {}'.format(path))
		for block in response.iter_content(1024):
			fd.write(block)
			display_progress(fd.tell(), 1, int(response.headers['Content-Length']))
	print('\nDownload completed.')


def get_source_list(args):
	if args is None:
		return list()
	lst = list()
	if '-' in args:
		for url in sys.stdin.readlines():
			lst.append(url)
	else:
		lst.extend(args)
	return lst


def url_to_hash(url):
	rawdata = get_torrent_file(url)
	return get_hash(rawdata)


def magnet_to_hash(magnet):
	match = re.search(r'xt=urn:btih:(.*?)(?:&.*)?$', magnet)
	return match.group(1)


def file_to_hash(path):
	with open(path, mode='rb') as fd:
		rawdata = fd.read()
	return get_hash(rawdata)


def source_to_hash(source):
	if source.startswith('http'):
		torrent_hash = url_to_hash(source)
	elif 'xt=urn:btih:' in source:
		torrent_hash = magnet_to_hash(source)
	elif os.path.exists(source):
		torrent_hash = file_to_hash(source)
	elif re.match('^[0-9a-fA-F]+$', source):
		torrent_hash = source
	else:
		print('Unknown source detected.', file=sys.stderr)
	return torrent_hash


def show_balance():
	response = requests.get('https://coinado.io/balance?u={}'.format(COINADO_SECRET))
	address = re.search(r'Bitcoin address: (?P<address>1[0-9a-zA-Z]+)', response.text, re.MULTILINE)
	balance = re.search(r'Balance: (?P<balance>.*)$', response.text, re.MULTILINE)
	pricing = re.search(r'Pricing: (?P<pricing>.*)$', response.text, re.MULTILINE)
	try:
		import sixel
	except ImportError:
		pass
	else:
		import io
		qrcode_image = requests.get(
			'https://chart.googleapis.com/chart?chs=250x250&cht=qr&chl={}'
			.format(address.group(1)))
		sixel_writer = sixel.SixelWriter()
		sixel_writer.draw(io.BytesIO(qrcode_image.content))
	print('Address: bitcoin:{}'.format(address.group(1)))
	print('QRcode: https://chart.googleapis.com/chart?chs=250x250&cht=qr&chl={}'.format(address.group(1)))
	print('Balance: {}'.format(balance.group(1)))
	print('Pricing: {}'.format(pricing.group(1)))


def dispatch_hash(args, t_hash):
	if args.filename:
		response = requests.head(get_endpoint(t_hash, args.select))
		match = re.search(r'''filename=['"](.*?)['"]''', response.headers['Content-Disposition'])
		print(match.group(1))
	elif args.endpoint:
		print(get_endpoint(t_hash, args.select))
	elif args.infohash:
		print(t_hash)
	else:
		if os.path.isfile(args.destination) and not args.force:
			print('To overwrite the file, please add --force option.', file=sys.stderr)
			return
		if args.quiet:
			sys.stdout = open(os.devnull, 'w')
		if args.all:
			if os.path.isdir(args.destination):
				for filename in get_filelist(t_hash):
					get_payload(t_hash, args.destination, filename, args.force)
			else:
				print('Destination is not directory. --all option contradicts.', file=sys.stderr)
				sys.exit()
		else:
			get_payload(t_hash, args.destination, args.select, args.force)


def setup_args():
	argparser = argparse.ArgumentParser()
	if len(sys.argv) == 1:
		argparser.print_usage()
	argparser.add_argument('torrent', nargs='*', help='url,hash,file,magnet...')
	argparser.add_argument('--quiet', action='store_true')
	g_source = argparser.add_argument_group(title='input option')
	g_select_or_all = g_source.add_mutually_exclusive_group()
	g_select_or_all.add_argument('--select', help='specify the filename which you want')
	g_select_or_all.add_argument('--all', action='store_true', help='download all file which is written in torrent file')
	g_source.add_argument('--stdin', action='store_true')
	g_dest = argparser.add_argument_group(title='output option')
	g_dest.add_argument('--destination', default=os.getcwd(), help='save files to this directory')
	g_dest.add_argument('--force', action='store_true', help='permit overwrite')
	g_info = argparser.add_argument_group(title='infomation option')
	g_info = g_info.add_mutually_exclusive_group()
	g_info.add_argument('--inquire', '--balance', action='store_true', help='show you account balance')
	g_info.add_argument('--filename', action='store_true', help='fetch filename')
	g_info.add_argument('--endpoint', action='store_true', help='fetch download url')
	g_info.add_argument('--infohash', action='store_true', help='calculate hash')
	args = argparser.parse_args()
	if args.torrent is None and args.stdin is not True:
		argparser.print_usage()
	return args


if __name__ == '__main__':
	args = setup_args()

	if args.inquire:
		show_balance()
		sys.exit()

	for source in args.torrent:
		t_hash = source_to_hash(source)
		dispatch_hash(args, t_hash)

	if args.stdin:
		while True:
			try:
				source = input()
			except EOFError:
				sys.exit()
			t_hash = source_to_hash(source)
			dispatch_hash(args, t_hash)
