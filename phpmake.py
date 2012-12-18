#!/usr/bin/env python
# -*- coding: utf-8 -*-

import argparse
import os
from glob import glob
import re
import json

USER_DIR = os.environ["HOME"] + '/.phpmake-master'

def get_patterns():
	if os.path.isdir(USER_DIR) is False:
		print "There is no directory '%s'." % USER_DIR
		print "Please set up phpmake first."
		print ""
		print "  $ phpmake install"
		exit(1)

	patterns = []

	for filename in glob(USER_DIR+'/*.php'):
		basename = os.path.basename(filename)
		if "?" in basename:
			pattern = re.sub(r"^[0-9]+_", "", basename)
			pattern = re.sub(r"\.php$", "", pattern)
			pattern = re.escape(pattern)
			pattern = pattern.replace("\?", ".+")
			pattern = "^" + pattern + "$"
			patterns.append({
				"pattern": pattern,
				"filename": filename
			})
			
	return patterns

def get_config_file():
	dir = os.getcwd()
	while dir != os.sep and dir:
		config_file = dir + '/.phpmake'

		if os.path.exists(config_file) and os.path.isfile(config_file):
			return config_file

		dir = os.path.dirname(dir)
	
	return False


def get_skelton_file(filename):
	patterns = get_patterns()
	for pattern in patterns:
		if re.match(re.compile(pattern["pattern"]), filename):
			return pattern["filename"]
	return False

def detect_namespace(config_file, default_namespace, namespace_separator):
	current_dir = os.popen("pwd").read().rstrip() # Call command becouse os.getcwd() is not case sensitive on MacOSX
	base_dir = len(os.path.dirname(os.path.dirname(config_file)))
	paths = current_dir[base_dir+1:].split(os.sep)

	if default_namespace is not None:
		paths[0] = default_namespace
	
	namespace = namespace_separator.join(paths)
	
	return namespace

def phpmake_init(args):

	if os.path.exists('.phpmake'):
		print "Already initialized."
		exit(1)

	print "Initializing..."
	master = open(USER_DIR+'/config.json', 'r')
	
	file = open('.phpmake', 'w')
	file.write(master.read())
	file.close()
	
	master.close()
	print ".phpmake was created."

def phpmake_new(args):

	config_file = get_config_file()

	if config_file is False:
		print "Config file not found."
		print "Please initialize at top directory of the namespace first."
		print ""
		print "  $ phpmake init"
		exit(1)
	
	try:
		file = open(config_file, 'r')
		config = json.loads(file.read())
		file.close()
	except ValueError, exception:
		print "Config file has syntax error: %s" % config_file
		print exception.message
		exit(1)
	
	filename = re.sub(r"\.php$", "", args.filename)
	
	if os.path.exists(filename + '.php'):
		print "Already script exists: %s.php" % filename
		exit(1)

	skelton_file = get_skelton_file(filename)

	if skelton_file is False:
		print "Skelton file not found for filename '%s'" % args.filename
		exit(1)
	
	file = open(skelton_file, 'r')
	contents = file.read()
	file.close()
	
	if 'replace' in config:
		variables = config['replace']
	else:
		variables = {}
	
	namespace = detect_namespace(config_file, config['namespace'], config['namespace_separator'])
	
	if config['namespace_separator'] == "\\":
		variables['__class__'] = filename
		variables['__namespace__'] = namespace
	else:
		variables['__class__'] = namespace + config['namespace_separator'] + filename
		variables['__namespace__'] = ""
		contents = contents.replace("namespace __namespace__;\n\n", "")

	for key, value in variables.items():
		contents = contents.replace(key, value)
	
	file = open(filename + '.php', 'w')
	file.write(contents)
	file.close()
	
	print "Script created: %s.php" % filename

def main():
	parser = argparse.ArgumentParser(description="PHP template file maker")

	subparsers = parser.add_subparsers(title='commands', metavar='command')

	command_init = subparsers.add_parser('init', help='initialize namespace')
	command_init.set_defaults(func=phpmake_init)

	command_new = subparsers.add_parser('new', help='create new PHP file')
	command_new.set_defaults(func=phpmake_new)
	command_new.add_argument("filename", type=str, help="script file name")

	args = parser.parse_args()
	args.func(args)

if __name__ == "__main__":
	main()
