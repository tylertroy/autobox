import os

import scaleapi
import json


def convert_to_bbox(annotation):
    """Convert a Scale API dictionary annotation to a string formatting
    the bbox according to the output from the Bbox-Label-Tool.
    """
    d = annotation
    coordinates = d['left'], d['top'], d['width'], d['height']
    coordinates = [ str(coordinate) for coordinate in coordinates ]
    return ' '.join(coordinates)

class NoTaskError(Exception):
    pass


class ScaleTaskManager(object):
    """A class to contain to create and handle Scale API tasks.
    """

    def __init__(self, session_path='', key=None):
        # Initialize client key.
        if not key: # Use test key.
            key = 'test_################################' # test key
        self.client = scaleapi.ScaleClient(key)
        self.tasks = []
        self.taskdir = os.path.join(session_path, 'label')
        self.logpath = os.path.join(session_path, 'log', 'scaleapi.log')

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

        scale_result = self.client.create_annotation_task(
            callback_url = callback_url,
            instruction = instruction,
            attachment_type = 'image',
            attachment = image_url,
            objects_to_annotate = objects_to_annotate,
            with_labels = False,
            examples = example
        ).param_dict

        name = os.path.basename(scale_result['params']['attachment'])
        print('{} task submitted.'.format(name))
        self.tasks.append(scale_result)

    def create_tasks_from_urls(self, image_urls):
        """Create bounding box tasks.
        """

        [ self.create_task(url) for url in image_urls ]

    def write_task_log(self):
        """Write results from Scale task creation to 'savepath'.
        """
        with open(self.logpath, 'w') as outfile:
            for task in self.tasks:
                json.dump(task, outfile)
                outfile.write('\n')

    def read_task_log(self):
        """Store image information in upload log as a json response.
        """
        
        with open(self.logpath, 'r') as f:
            self.tasks = [ json.loads(line) for line in f.readlines() ]

        # Update task information from saved task ids.
        self.tasks_info()

    def tasks_ids(self):
        """Return the task ids from self.tasks.
        """
        
        return [ task['task_id'] for task in self.tasks ]

    def tasks_info(self):
        """Save tasks to self.tasks from task ids.
        """

        task_ids = self.tasks_ids()

        self.tasks = [ self.client.fetch_task(task_id).param_dict 
            for task_id in task_ids ]

    def tasks_complete(self):
        """Return True if all tasks are complete.
        """

        return all([ task['status'] == 'completed' for task in self.tasks ])

    def tasks_pending_names(self):
        """Return list of incomplete tasks.
        """
        pending = []
        for task in self.tasks:
            if task['status'] == 'pending':
                task_id = task['task_id']
                name = self.task_name(task)
                pending.append((task_id, name))

        return pending

    def tasks_pending(self):
        """Return the list of incomplete tasks."""
        return [ task for task in self.tasks if task['status'] == 'pending' ]

    def write_annotations_to_bbox(self):
        """Write the annotated bounding boxes from scale to a txt file.
        """
        for task in self.tasks:
            name = self.task_name(task)
            name = os.path.splitext(name)[0] + '.txt'
            path = os.path.join(self.taskdir, name)

            annotations = task['response']['annotations']

            string = [str(len(annotations))]
            coordinates = [ convert_to_bbox(annotation) 
                                        for annotation in annotations ]
            
            with open(path, 'w') as f:
                string = '\n'.join(string + coordinates + ['\n'])
                f.write(string)

            print('{} bbox saved.'.format(name))

    def save_completed_tasks(self):
        """Check if all tasks are completed and save task annotations.
        """

        if not self.tasks:
            raise NoTaskError('No tasks are loaded. Try self.read_task_log first.')

        if self.tasks_complete():
            self.write_annotations_to_bbox()
            return True
        
        for task_id, name in self.tasks_pending_names():
            print('{} incomplete!'.format(name))

        return False

    def cancel_pending_tasks(self):
        """Cancel a incomplete task by task id.
        """
        tasks = self.tasks_pending_names()
        if not tasks:
            print('No pending tasks in this session.')
        for task_id, name in tasks:
            self.client.cancel_task(task_id)
            print('{} task cancelled.'.format(name))

    @staticmethod
    def task_name(task):
        """Return a task name.
        """
        return os.path.basename(task['params']['attachment'])


if __name__ == '__main__':


    key = 'test_################################' # test key
    stm = ScaleTaskManager(key)
    stm.create_task(url)
    stm.write_task_log()
    stm.read_task_log()
    stm.get_completed_tasks('./test')