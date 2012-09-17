from appscript import app, k
from appscript.reference import Reference

__all__ = ['omnifocus']


CACHE = {}


class collection(object):

    def __init__(self, f):
        self._getitem = None
        self._f = f
        self._instance = None

    def __get__(self, instance, cls):
        self._f = self._f.__get__(instance, cls)
        self._getitem = self._getitem.__get__(instance, cls)
        return self

    def __call__(self):
        return self.all()

    def __iter__(self):
        return self.all()

    def all(self):
        return self._f()

    def getitem(self, getitem):
        self._getitem = getitem

    def __getitem__(self, item):
        if self._getitem is None:
            raise AttributeError('__getitem__')
        return self._getitem(item)


def get_prop_value(prop):
    result = prop.get() if isinstance(prop, Reference) else prop
    return result if result != k.missing_value else None


def ref_property(name, ro=False, getter=None, setter=None):

    if getter is None:
        def getter(self):
            prop = getattr(self._ref, name)
            return get_prop_value(prop)

    if setter is None:
        def setter(self, value):
            prop = getattr(self._ref, name)
            prop.set(value)

    if ro:
        return property(getter)
    else:
        return property(getter, setter)


class OFObject(object):
    
    def __new__(cls, reference):
        return CACHE.setdefault(reference, object.__new__(cls, reference))

    def __del__(self):
        try:
            del CACHE[self._ref]
        except (AttributeError, TypeError):
            pass

    def __init__(self, reference):
        self._ref = reference

    id = ref_property("id", ro=True)


class Contained(object):

    ContainerClass = None

    name = ref_property("name")

    @property
    def root(self):
        ob = self
        while ob:
            if isinstance(ob, OmniFocus):
                break
            ob = self.container
        return ob

    @property
    def fqdn(self):
        ob = self
        names = []
        while ob and not isinstance(ob, OmniFocus):
            names.append(ob.name)
            ob = ob.container
        return ' : '.join(reversed(names))

    @property
    def container(self):
        if not self.ContainerClass:
            return None
        return self.ContainerClass(self._ref.container.get())

    def delete(self):
        self.container._ref.delete(self._ref)

    def __repr__(self):
        return "<{klass} '{fqdn}'>".format(klass=self.__class__.__name__,
                                           fqdn=self.fqdn)


class TaskContainer(object):

    @property
    def flattened_tasks(self):
        return (Task(r) for r in self._ref.flattened_tasks.get())

    @collection
    def tasks(self):
        return (Task(r) for r in self._ref.tasks.get())

    @tasks.getitem
    def _task_getitem(self, item):
        return Task(self._ref.tasks[item])

    note = ref_property('note')
    completed_by_children = ref_property('completed_by_children')
    sequential = ref_property('sequential')
    flagged = ref_property('flagged')
    blocked = ref_property('blocked', ro=True)
    creation_date = ref_property("creation_date")
    modification_date = ref_property("modification_date", ro=True)

    start_date = ref_property("start_date")
    due_date = ref_property("due_date")
    completion_date = ref_property("completion_date")
    completed = ref_property("completed")

    estimated_minutes = ref_property("estimated_minutes")

    #TODO: Make repetion_rule rw with repetition_interval
    repetition_rule = ref_property("repetition_rule", ro=True)

    number_of_tasks = ref_property("number_of_tasks", ro=True)
    number_of_available_tasks = ref_property('number_of_available_tasks',
                                             ro=True)
    number_of_completed_tasks = ref_property('number_of_completed_tasks',
                                             ro=True)

    @property
    def context(self):
        value = get_prop_value(self._ref.context)
        if value is not None:
            return Context(value)

    @context.setter
    def context(self, context):
        if context is None:
            self._ref.context.set(k.missing_value)
        elif not isinstance(context, Context):
            raise ValueError("Can't set a context to a non-context")
        else:
            self._ref.context.set(context._ref)

    def _task_props(self, name, note=None, context=None, flagged=False,
                    completed=False, completed_by_children=False,
                    sequential=False, start_date=None, due_date=None,
                    creation_date=None, completion_date=None,
                    estimated_minutes=None):
        props = {k.name: name, 
                 k.flagged: flagged, 
                 k.sequential: sequential,
                 k.completed: completed, 
                 k.completed_by_children: completed_by_children}
        if note is not None:
            props[k.note] = note
        if context is not None:
            props[k.context] = context._ref
        if start_date is not None:
            props[k.start_date] = start_date
        if due_date is not None:
            props[k.due_date] = due_date
        if creation_date is not None:
            props[k.creation_date] = creation_date
        if completion_date is not None:
            props[k.completion_date] = completion_date
        if estimated_minutes is not None:
            props[k.estimated_minutes] = int(estimated_minutes)
        return props

    def create_task(self, name, note=None, context=None, flagged=False,
                    completed=False, completed_by_children=False,
                    sequential=False, start_date=None, due_date=None,
                    creation_date=None, completion_date=None,
                    estimated_minutes=None):
        props = self._task_props(name, note, context, flagged, completed,
                                 completed_by_children, sequential, start_date,
                                 due_date, creation_date, completion_date,
                                 estimated_minutes)
        task = self._ref.make(new=k.task, with_properties=props)
        return Task(task)


    def create_inbox_task(self, name, note=None, context=None, flagged=False,
                    completed=False, completed_by_children=False,
                    sequential=False, start_date=None, due_date=None,
                    creation_date=None, completion_date=None,
                    estimated_minutes=None):
        props = self._task_props(name, note, context, flagged, completed,
                                 completed_by_children, sequential, start_date,
                                 due_date, creation_date, completion_date,
                                 estimated_minutes)
        task = self.root._ref.make(new=k.inbox_task, with_properties=props)
        return InboxTask(task)
    


class Section(OFObject, Contained):

    @property
    def flattened_projects(self):
        return (Project(r) for r in self._ref.flattened_projects.get())

    @collection
    def projects(self):
        return (Project(r) for r in self._ref.projects.get())

    @projects.getitem
    def _project_getitem(self, item):
        return Project(self._ref.projects[item])

    @property
    def flattened_folders(self):
        return (Folder(r) for r in self._ref.flattened_folders.get())

    @collection
    def folders(self):
        return (Folder(r) for r in self._ref.folders.get())

    @folders.getitem
    def _folder_getitem(self, item):
        return Folder(self._ref.folders[item])

    @property
    def flattened_tasks(self):
        return (Task(r) for r in self._ref.flattened_tasks.get())

    @collection
    def tasks(self):
        return (Task(r) for r in self._ref.tasks.get())

    @tasks.getitem
    def _task_getitem(self, item):
        return Task(self._ref.tasks[item])

    @property
    def container(self):
        return Folder(self._ref.container.get())

    @property
    def fqdn(self):
        ob = self
        names = []
        while not isinstance(ob, OmniFocus):
            names.append(ob.name)
            ob = ob.container
        return ' : '.join(reversed(names))

    def get_project(self, id_):
        for p in self.root.flattened_projects:
            if p.id == id_:
                return p
        return None

    def find_projects(self, query, max=0):
        fqdn = self.fqdn
        if fqdn:
            query = '{fqdn} : {query}'.format(fqdn=fqdn, query=query)
        results = self.root._ref.complete(query, as_=k.project,
                                          maximum_matches=max)
        results = iter(results)
        result = results.next()
        while result.get(k.score):
            yield self.get_project(result.get(k.id))
            result = results.next()


class Folder(Section):

    @property
    def ContainerClass(self):
        return Folder

    note = ref_property("note")
    hidden = ref_property("hidden")
    effectively_hidden = ref_property("effectively_hidden", ro=True)
    creation_date = ref_property("creation_date", ro=True)
    modification_date = ref_property("modification_date", ro=True)

    def create_folder(self, name):
        ref = self._ref.make(new=k.folder, with_properties={k.name:name})
        return Folder(ref)

    def create_project(self, name):
        ref = self._ref.make(new=k.project, with_properties={k.name:name})
        return Project(ref)


class Task(OFObject, TaskContainer, Contained):

    def __new__(cls, reference):
        if get_prop_value(reference.in_inbox):
            cls = InboxTask
        return OFObject.__new__(cls, reference)

    in_inbox = ref_property("in_inbox", ro=True)

    @property
    def containing_project(self):
        value = get_prop_value(self._ref.containing_project)
        if value:
            value = Project(value)
        return value

    @property
    def parent_task(self):
        value = get_prop_value(self._ref.parent_task)
        if value:
            value = Task(value)
        return value

    @property
    def container(self):
        task = self.parent_task
        return self.containing_project if task is None or task.parent_task is None else task


class InboxTask(Task):

    @property
    def assigned_container(self):
        ref = get_prop_value(self._ref.assigned_container)
        return Project(ref)

    @assigned_container.setter
    def assigned_container(self, value):
        if value is None:
            self._ref.assigned_container.set(k.missing_value)
        elif not isinstance(value, TaskContainer):
            raise ValueError("Can't put a task in a non-TaskContainer")
        else:
            self._ref.assigned_container.set(value._ref)


class Project(Section, TaskContainer):

    STATUSES = {
        k.active: (0, 'Active'),
        k.on_hold: (1, 'On Hold'),
        k.done: (2, 'Done'),
        k.dropped: (3, 'Dropped')
    }

    @property
    def next_task(self):
        ref = self._ref.next_task.get()
        if ref == k.missing_value:
            return None
        return Task(ref)

    def _get_status(self):
        return get_prop_value(self._ref.status)

    @property
    def status(self):
        return Project.STATUSES[self._get_status()][0]

    @property
    def status_name(self):
        return Project.STATUSES[self._get_status()][1]


    last_review_date = ref_property('last_review_date')
    next_review_date = ref_property('next_review_date')
    #TODO: Make review_interval rw with repetition_interval
    review_interval = ref_property('review_interval', ro=True)
    singleton_action_holder = ref_property('singleton_action_holder')
    default_singleton_action_holder = ref_property('default_singleton_action_holder')


class Context(OFObject, Contained):

    @property
    def ContainerClass(self):
        return Context

    @property
    def flattened_contexts(self):
        return (Context(r) for r in self._ref.flattened_contexts.get())

    @property
    def contexts(self):
        return (Context(r) for r in self._ref.contexts.get())

    @property
    def container(self):
        return Context(self._ref.container.get())

    def get_context(self, id_):
        for c in self.root.flattened_contexts:
            if c.id == id_:
                return c
        return None

    def find_contexts(self, query, max=0):
        fqdn = self.fqdn
        if fqdn:
            query = '{fqdn} : {query}'.format(fqdn=fqdn, query=query)
        results = self.root._ref.complete(query, as_=k.context,
                                          maximum_matches=max)
        results = iter(results)
        result = results.next()
        while result.get(k.score):
            yield self.get_context(result.get(k.id))
            result = results.next()

    note = ref_property('note')
    allows_next_action = ref_property('allows_next_action')
    hidden = ref_property('hidden')
    effectively_hidden = ref_property("effectively_hidden", ro=True)
    available_task_count = ref_property("available_task_count", ro=True)
    remaining_task_count = ref_property("remaining_task_count", ro=True)
    # TODO: Make location rw with k.location_information
    location = ref_property("location", ro=True)

    def create_context(self, name, note=None, allows_next_action=None,
                       hidden=None):
        # TODO: Location
        props = {k.name:name}
        if note:
            props[k.note] = note
        if allows_next_action is not None:
            props[k.allows_next_action] = allows_next_action
        if hidden is not None:
            props[k.hidden] = hidden
        ref = self._ref.make(new=k.context, with_properties=props)
        return Context(ref)


class OmniFocus(Section, Context):

    @collection
    def inbox_tasks(self):
        return (InboxTask(r) for r in self._ref.inbox_tasks.get())

    @inbox_tasks.getitem
    def _inbox_task_getitem(self, item):
        return InboxTask(self._ref.inbox_tasks[item])


class Perspective(OFObject):
    pass


# The singleton!
omnifocus = OmniFocus(app(u'OmniFocus.app').default_document.get())
