#!/usr/bin/env python
# -*- coding: utf-8 -*- #

# Copyright (c) 2015, Kaoru Esashika
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without modification, are permitted provided that the following conditions are met:
#
# 1. Redistributions of source code must retain the above copyright notice, this list of conditions and the following disclaimer.
#
# 2. Redistributions in binary form must reproduce the above copyright notice, this list of conditions and the following disclaimer in the documentation and/or other materials provided with the distribution.
#
# 3. Neither the name of the copyright holder nor the names of its contributors may be used to endorse or promote products derived from this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.


import sys
import os
import re
import hashlib
import argparse
import requests
import bencodepy


COINADO_SECRET = os.getenv('COINADO_SECRET')


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
		endpoint = 'https://coinado.io/i/{}/search/{}?u={}'.format(torrent_hash, select, COINADO_SECRET)
	else:
		endpoint = 'https://coinado.io/i/{}/auto?u={}'.format(torrent_hash, COINADO_SECRET)
	return endpoint


def get_payload(torrent_hash, dest_path, select=None):

	def spinning_cursor():
		while True:
			for cursor in r'|/-\\':
				yield cursor
	spinner = spinning_cursor()

	def display_progress(count, size, total):
		percentage = count * size / total
		sys.stdout.write('\r{} {:.3%} ({}/{} bytes) downloaded.'.format(next(spinner), percentage, count * size, total))
		sys.stdout.flush()

	endpoint = get_endpoint(torrent_hash, select)
	print('Connecting...')
	response = requests.get(endpoint, stream=True)
	if os.path.isdir(dest_path):
		match = re.search(r'''filename=['"](.*?)['"]''', response.headers['Content-Disposition'])
		filename = match.group(1)
		path = os.path.join(os.path.abspath(dest_path), filename)
	else:
		path = os.path.abspath(dest_path)

	with open(path, mode='wb') as fd:
		print('Connected.')
		print('filepath: {}'.format(fd.path))
		for block in response.iter_content():
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


def url_to_hash(urls):
	if urls is None:
		return
	hashes = list()
	for url in urls:
		rawdata = get_torrent_file(url)
		hashes.append(get_hash(rawdata))
	return hashes


def magnet_to_hash(magnets):
	if magnets is None:
		return
	hashes = list()
	for magnet in magnets:
		match = re.search(r'xt=urn:btih:(.*?)(?:&.*)?$', magnet)
		hashes.append(match.group(1))
	return hashes


def file_to_hash(files):
	if files is None:
		return
	hashes = list()
	for f in files:
		with open(f, mode='rb') as fd:
			rawdata = fd.read()
		hashes.append(get_hash(rawdata))
	return hashes


def setup_args():
	argparser = argparse.ArgumentParser()
	if len(sys.argv) == 1:
		argparser.print_usage()
	argparser.add_argument('torrent', nargs='*')
	argparser.add_argument('--quiet', action='store_true')
	g_source = argparser.add_argument_group(title='input option')
	g_source.add_argument('--url', '--uri', nargs='+')
	g_source.add_argument('--hash', nargs='+')
	g_source.add_argument('--magnet', nargs='+')
	g_source.add_argument('--file', nargs='+')
	g_source.add_argument('--select')
	g_dest = argparser.add_argument_group(title='output option')
	g_dest.add_argument('--destination', default=os.getcwd())
	g_info = argparser.add_argument_group(title='infomation option')
	g_info = g_info.add_mutually_exclusive_group()
	g_info.add_argument('--filename', action='store_true', help='fetch filename')
	g_info.add_argument('--endpoint', action='store_true', help='fetch download url')
	g_info.add_argument('--info_hash', action='store_true', help='calculate hash')
	args = argparser.parse_args()
	return args


if __name__ == '__main__':
	args = setup_args()

	if args.quiet:
		sys.stdout = open(os.devnull, 'w')

	torrent_hashes = set()
	torrent_hashes.update(url_to_hash(get_source_list(args.url)))
	torrent_hashes.update(get_source_list(args.hash))
	torrent_hashes.update(magnet_to_hash(get_source_list(args.magnet)))
	torrent_hashes.update(file_to_hash(get_source_list(args.file)))
	for link in args.torrent:
		if link.startswith('http'):
			torrent_hashes.update(url_to_hash([link]))
		elif 'xt=urn:btih:' in link:
			torrent_hashes.update(magnet_to_hash([link]))
		elif os.path.exists(link):
			torrent_hashes.update(file_to_hash([link]))
		elif re.match('^[0-9a-fA-F]+$', link):
			torrent_hashes.update([link])
		else:
			raise RuntimeError('Unknown source detected.')

	for t_hash in torrent_hashes:
		if args.filename:
			response = requests.head(get_endpoint(t_hash, args.select))
			match = re.search(r'''filename=['"](.*?)['"]''', response.headers['Content-Disposition'])
			print(match.group(1))
		elif args.endpoint:
			print(get_endpoint(t_hash, args.select))
		elif args.info_hash:
			print(t_hash)
		else:
			get_payload(t_hash, args.destination, args.select)