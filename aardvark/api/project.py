from aardvark.api.rest import keystone
from aardvark.objects import project as pr_obj

class Project(object):

    def __init__(self, id_, name, preemptible=False):
        self.id_ = id_
        self.name = name
        self.client = keystone.KeystoneClient()


class ProjectList(object):

    def __init__(self):
        self.client = keystone.KeystoneClient()

    @property
    def projects(self):
        # Pluggable filters
        projects = []
        for project in self.client.get_projects():
            try:
                projects.append(pr_obj.Project(
                    project['id'], project['name'], project['preemptible'])) 
            except KeyError:
                projects.append(pr_obj.Project(
                    project['id'], project['name']))
        return projects

    @property
    def preemptible_projects(self):
        # Pluggable filters
        projects = []
        for project in self.client.get_projects(tags=['preemptible']):
            projects.append(pr_obj.Project(
                project['id'], project['name'], preemptible=True))
        return projects
