from __future__ import print_function

import os
import sys
import warnings
import urllib3
import json	

import cloudinary
import cloudinary.uploader
import cloudinary.api


class ImageIdNotFound(Exception):
    pass


def listpaths(path, ext=''):
	"""Return full paths to files in path if filter text in path.
	"""
	os.listdir(path)
	paths = [ os.path.join(path, name) 
	    for name in os.listdir(path) if ext in name ]
	return paths


def upload(path):
	"""Upload a local image to the cloudinary database.
	"""
	
	# Public id is the name of the image.
	public_id = os.path.splitext(os.path.basename(path))[0]
	# img = open(path, 'rb')
	
	with open(path, 'rb') as img:
		response = cloudinary.uploader.upload(img, public_id=public_id)
	
	public_id = response['public_id']
	url = response['url']
	message = 'Uploaded {} to {}.'.format(public_id, url)
	print(message)

	return response


def delete(public_id):
	"""Delete an image with public_id from cloudinary.
	"""

	# Invalidation removes access to cached images on the server.
	result = cloudinary.uploader.destroy(public_id, invalidate=True)
	
	if result['result'].decode('utf-8') == 'ok':
		message = 'Deleted {} from cloudinary.'.format(public_id)
		print(message)
	else:
		message = '{} not found!'.format(public_id) 
		warnings.warn(message)



class CloudinaryUpload(object):
	"""Methods for handling interaction with the cloudinary API.
	"""

	# Disable lack of security cerificate warning.
	urllib3.disable_warnings()
	
	def __init__(self, session_path='', cloud_name='', api_key='', api_secret=''):	
		"""Configure cloudinary with API codes for image uploading."""
		
		super(CloudinaryUpload, self).__init__()
		
		defaults = [ 
			"_________",					# Cloud name.
			"_______________", 				# API key.
			"___________________________"	# API secret.
			]
	
		args = [ cloud_name, api_key, api_secret ]
	
		args = [ default if not arg else arg 
						    for default, arg in zip(defaults, args) ]

		self.cloud_name, self.api_key, self.api_secret = args

		self.session_path = session_path
		self.log_path = os.path.join(session_path, 'log', 'cloudinary.log')
		self.bbox_path = os.path.join(session_path, 'bbox')

		cloudinary.config( 
			cloud_name = self.cloud_name, 
			api_key = self.api_key, 
			api_secret = self.api_secret
			)

		self.responses = []
		self.uploads = []
	


	def from_directory(self, path, ext='jpg'):
		"""Upload images in path with extension, ext.
		"""
		self.paths = listpaths(path, ext='jpg')
		self.responses = [ upload(path) for path in self.paths ]

	def delete_images_from_log(self):
		"""Delete images from their public id stored in upload log.
		"""
		# print(self.responses)
		public_ids = self.get_public_ids()

		[ delete(public_id) for public_id in public_ids ]
		

	def write_upload_log(self):
		"""Save upload result log to 'savepath'.
		"""

		with open(self.log_path, 'w') as outfile:
			for response in self.responses:
				json.dump(response, outfile)
				outfile.write('\n')


	def read_upload_log(self):
		"""Store image information in upload log as a json response.
		"""
		
		with open(self.log_path, 'r') as f:
			self.responses = [ json.loads(line) for line in f.readlines() ]

		self.get_image_infos()

	def get_image_urls(self):
		"""Return URL data from cloudinary upload results.
		"""
		
		return [ response['url'] for response in self.responses ]


	def get_public_ids(self):
		"""Return id data from cloudinary upload results.
		"""
		return [ response['public_id'] for response in self.responses ]

	def get_image_infos(self):
		"""Set self.response to the image info from request.
		"""
		public_ids = self.get_public_ids()
		self.responses = [ cloudinary.api.resource(public_id) 
						   for public_id in public_ids ]


if __name__ == '__main__':
	
	# Path to images for upload.
	path = './img'
	
	# Set up Cloudinary API instance.
	image_upload = CloudinaryUpload()
	
	# Upload all images in path and save responses to self.responses
	image_upload.from_directory(path)
	
	# Save upload information to a log file for later retrieval.
	image_upload.write_upload_log(savepath='cloudinary.log')
	
	# Read json upload response data from upload log.
	image_upload.read_upload_log('cloudinary_log.txt')
	
	# Return a list of img urls.
	image_upload.get_image_urls()
	
	# Delete images referenced in self.responses.
	image_upload.delete_images_from_log()
	
