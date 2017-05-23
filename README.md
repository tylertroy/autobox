# Autobox
An automated data labeling command-line script for the preparation of machine learning data.

## Description

Autobox was designed to automate the arduous task of defining bounding boxes around objects of interest in an image. It was made for preparing training data for use with training convolutional neural networks in particular the [YOLO](https://pjreddie.com/darknet/yolo/) model.

This python script creates a convenient script-based front end wrapping APIs from the [Cloudinary](http://cloudinary.com/) image hosting service and the [ScaleAPI](https://www.scaleapi.com/) human task service.

After setting up these accounts you simply point the script to your directory of images to be annotated.  

## Requirements

* Python 2.7+
* Coudinary python libraries (install with pip)
* ScaleAPI python libraries (install with pip)
* Account with Cloudinary (Free)
* Account with ScaleAPI (Free to create but tasks are paid _per rata_)

## Setup

You should first determine your authentication credentials for both Cloudinary and ScaleAPI and update `wrap_cloud.py` and `wrap_scale.py` according to the following.

### `wrap_cloud.py` (Cloudinary)

In the `CloudinaryUpload` class, modify `defaults` with your cloudinary authentication details.

```python
def __init__(self, session_path='', cloud_name='', api_key='', api_secret=''):	
  """Configure cloudinary with API codes for image uploading."""
  defaults = [ 
    "#########",                   # Cloud name.
    "###############",             # API key.
    "###########################"  # API secret.
    ]
```

### `wrap_scale.py` (ScaleAPI)

In the `ScaleTaskManager` class, modify `key` with your ScaleAPI key.

```python
def __init__(self, session_path='', key=None):
    # Initialize client key.
    if not key: # Use hardcoded key below.
        key = 'test_################################' # Your key.
```

Modify `callback_url`, `instruction`, `objects_to_annotate`, and `example` in `ScaleTaskManager.create_task` to reflect the requirements for your image labelling task. See [here](https://docs.scaleapi.com/#create-image-annotation-task) for more details on these variables,

```python
def create_task(self, image_url):
    """Create a bounding box task with scale API.
    """
    callback_url = 'https://yourapp.herokuapp.com/'
    instruction = 'Draw a box around all persons in the image.'
    objects_to_annotate = ['person']
    example = [
            {
                'correct': True,
                'image': 'http://imgur.com/a/correctimage',
                'explanation': 'The boxes are tight and accurate'
            },
            {
                'correct': False,
                'image': 'http://imgur.com/a/falseimage',
                'explanation': 'The boxes are neither accurate nor complete'
            }
        ]
```

## Usage

Autobox consists of a series of methods for handling the process. These are described by running the script without arguments but are reproduced here for convenience.

```bash
./autobox.py <method> <args>
```
### Methods (create, retrieve, cancel, delete)


#### create
```bash
./autobox.py create /path/to/session /path/to/images/
```

* Create directories at /path/to/session/ -> ./log ./label
* Upload images in /path/to/images/ to the cloudinary server 
* Submit bounding box tasks to Scale API. 
* Save cloudinary.log and scaleapi.log to 'path/to/session/log' 

_N.B. Task logs are used to cancel, retrieve, and delete tasks from a session._

#### retrieve
```bash
./autobox.py retrieve /path/to/session
```

* Retrieve tasks listed in '/path/to/session/log/scaleapi.log' from Scale API server.
* If tasks are completed save task bounding boxes to '/path/to/session/label/'


#### cancel
```bash
./autobox.py cancel /path/to/session
```

* Cancel all incomplete tasks in this session.

#### close
```bash
./autobox.py close /path/to/session
```

* Delete images listed in '/path/to/session/log/cloudinary.log' from cloudinary server.
