#!/usr/bin/python

'''
autobox is used to create bounding box tasks with the scale API.

Usage:

./autobox.py <method> <args>

<method> --> create, retrieve, cancel, delete


create

./autobox.py create /path/to/session /path/to/images/

- Create directories at /path/to/session/ -> ./log ./label
- Upload images in /path/to/images/ to the cloudinary server 
- Submit bounding box tasks to Scale API. 
- Save cloudinary.log and scaleapi.log to 'path/to/session/log'
  N.B. Task logs are used to cancel, retrieve, and delete
  tasks from a session.


retrieve

./autobox.py retrieve /path/to/session

- Retrieve tasks listed in '/path/to/session/log/scaleapi.log' 
  from Scale API server.
- If tasks are completed save task bounding boxes to 
  '/path/to/session/label/'


cancel

./autobox.py cancel /path/to/session

- Cancel all incomplete tasks in this session.


close

./autobox.py close /path/to/session

- Delete images listed in '/path/to/session/log/cloudinary.log' 
  from cloudinary server.
'''

# Python 2/3 compatibility
from __future__ import print_function

import sys
import os
import shutil

import wrap_cloud
import wrap_scale


class DirectoryExists(Exception):
	pass

class DirectoryNotExists(Exception):
	pass

def initialize_session(session_path=''):
	"""Create a new feature labeling session.
	"""
	if os.path.exists(session_path):
		message = '{} already exists. Remove this directory or choose a unique name.'
		raise DirectoryExists(message.format(session_path))

	log = os.path.join(session_path,'log')
	label = os.path.join(session_path, 'label')
	
	os.mkdir(session_path)
	os.mkdir(log)
	os.mkdir(label)

	print('Created new session at {}'.format(session_path))

def confirm_delete_images(session_path=''):
	"""Confirm with user the deletion of the session.
	"""
	
	if not os.path.exists(session_path):
		message = '{} does not exit. Check your session path name.'
		raise DirectoryExists(message.format(session_path))

	message = '\n'.join((
		'This process will perform the following irreversible actions:',
	    'Delete images from Cloudinary server.',
	    'Cancel pending ScaleAPI tasks.',
	    ))
	print(message)

	input_func = { 2: raw_input, 3: input }
	option = input_func[sys.version_info.major]('Proceed (Y/n) ')

	if option != 'Y':
		print('Deletion of session at {} aborted.'.format(session_path))
		return False

	print('Session at {} deleted.'.format(session_path))
	return True

def method_create(session_path, img_path):
	"""Create a new labelling session at 'session_path' using images at
	'img_path'.
	"""

	# Initialize image upload and labeling session.
	initialize_session(session_path)
	
	# Set up Cloudinary API and ScaleAPI instances.
	cloudup = wrap_cloud.CloudinaryUpload(session_path)
	stm = wrap_scale.ScaleTaskManager(session_path=session_path)
	
	# Cloudinary functions.

	cloudup.from_directory(img_path)
	cloudup.write_upload_log()
	image_urls = cloudup.get_image_urls()
	
	# ScaleAPI functions

	stm.create_tasks_from_urls(image_urls)
	stm.write_task_log()

def method_retrieve(session_path):
	"""Retrieve the bounding box annotations from ScaleAPI."""
	stm = wrap_scale.ScaleTaskManager(session_path)
	stm.read_task_log()
	if stm.save_completed_tasks():
		session_path += '/log/label'
		print('Complete! labels saved to {}'.format(session_path))
	else:
		print('Incomplete! No labels saved.'.format(session_path))
		

def method_cancel(session_path):
	"""Cancel all pending Scale API jobs in this session.
	"""
	stm = wrap_scale.ScaleTaskManager(session_path)
	stm.read_task_log()
	stm.cancel_pending_tasks()
	

def method_close(session_path):
	"""Delete all session images from Cloudinary.
	"""
	if confirm_delete_images(session_path):
		stm = wrap_scale.ScaleTaskManager(session_path)
		stm.cancel_pending_tasks()
		cloudup = wrap_cloud.CloudinaryUpload(session_path)
		cloudup.read_upload_log()
		cloudup.delete_images_from_log()


if __name__ == '__main__':
	
	# Derive method from argv. See __doc__.
	try:
		method = sys.argv[1]
	except (ValueError, IndexError):
		print(__doc__)
		quit()

	methods = {
	    'create'   : method_create,
	    'retrieve' : method_retrieve,
	    'cancel'   : method_cancel,
	    'close'    : method_close
	    }
	 
	args = sys.argv[2:]
	methods[method](*args)
