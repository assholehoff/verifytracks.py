#!/usr/bin/env python

# Anton Dahlén, updated 2022-11-22

import argparse
import json
import os
import subprocess
import sys
from termcolor import colored

def parsearguments(argv):
	parser = argparse.ArgumentParser(
		prog = 'verifytracks',
		description = 'Check that the audio and video tracks are roughly the same length.',
	)
	parser.add_argument('-q', '--quiet', action='store_true', default=False, dest='quiet', help='supress output')
	parser.add_argument('-t', '--tolerance', action='store', type=int, default=2000, dest='tolerance', help='tolerance for reporting pass, in milliseconds')
	parser.add_argument('filename', nargs='*', help='file(s) to verify')
	
	argv = parser.parse_args()

	filename = argv.filename
	quiet = argv.quiet
	tolerance = argv.tolerance
	
	return filename, quiet, tolerance

def convertms(milliseconds):
	hours = milliseconds // 3600000
	milliseconds = milliseconds % 3600000
	minutes = milliseconds // 60000
	milliseconds = milliseconds % 60000
	seconds = milliseconds // 1000
	milliseconds = milliseconds % 1000
	time_string = ''
	if hours > 0:
		time_string += str(hours) + 'h'
	if minutes > 0 or hours > 0:
		time_string += str(minutes) + 'm'
	if seconds > 0 or minutes > 0:
		time_string += str(seconds) + 's'
	if milliseconds > 0:
		time_string += str(milliseconds) + 'ms'
	return colored(time_string, 'yellow')

def verifytracks(file, tolerance):
	audio_tracks, video_tracks = [], []
	video_duration = 0
	command_array = [ "ffprobe", "-hide_banner", "-show_streams", "-print_format", "json", file ]
	command_process = subprocess.run(command_array, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
	data = json.loads(command_process.stdout)
	difference = 0
	passed = True

	for stream in data["streams"]:
		if (stream['codec_type'] == 'audio'):
			audio_tracks.append(int(float(stream['duration']) * 1000))
		elif (stream['codec_type'] == 'video') and (stream['codec_name'] != 'mjpeg') and (stream['codec_name'] != 'png'):
			video_tracks.append(int(float(stream['duration']) * 1000))

	for audio_duration in audio_tracks:
		_difference = abs(audio_duration - video_tracks[0])
		if _difference > tolerance:
			difference = _difference
			passed = False

	time_string = 'difference: ' + convertms(difference)
	track_string = str(len(video_tracks)) + '+' + str(len(audio_tracks)) + ' track'

	if len(audio_tracks) == 0:
		passed = False
		time_string = colored('NO AUDIO TRACKS FOUND', 'red')

	if len(audio_tracks) > 1 or len(audio_tracks) == 0:
		track_string += 's: '
	else:
		track_string += ':  '

	return passed, track_string, time_string

if __name__ == '__main__':
	def main(argv):
		files, quiet, tolerance = parsearguments(argv)
		files_passed = True
		messages = []

		for file in files:
			verification_passed, audio_tracks, time_string = verifytracks(file, tolerance)
			filename = str(os.path.basename(file))
			if verification_passed:
				passed = colored('PASSED: ', 'green')
				tracks = colored(audio_tracks, 'yellow')
				messages.append(passed + tracks + filename)
			else:
				files_passed = False
				failed = colored('FAILED: ', 'red')
				tracks = colored(audio_tracks, 'red')
				difference = ' (' + time_string + ') '
				messages.append(failed + tracks + filename + difference)

		if not quiet:
			for message in messages:
				print(message)

		if files_passed:
			return 0
		else:
			return -1

main(sys.argv)