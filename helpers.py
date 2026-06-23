from models import Task, GroupTask

def sort_tasks(tasks: list[Task]):
    
    not_done_with_deadline = [task for task in tasks if not task.is_done and task.deadline]
    not_done_no_deadline = [task for task in tasks if not task.is_done and not task.deadline]
    done = [task for task in tasks if task.is_done]

    not_done_with_deadline.sort(key = lambda task: (task.deadline, task.title.lower()))
    not_done_no_deadline.sort(key = lambda task: task.title.lower())
    done.sort(key = lambda task: task.title.lower())
   
    return not_done_with_deadline + not_done_no_deadline + done


def sort_groups(groups: list[GroupTask]):
    completed_groups = [group for group in groups if group.progress[0] == group.progress[1] and group.progress[1] != 0]
    incomplete_groups = [group for group in groups if group.progress[0] != group.progress[1] or group.progress[1] == 0]
    
    completed_groups.sort(key = lambda group: group.title.lower())
    incomplete_groups.sort(key = lambda group: group.title.lower())
    
    return (completed_groups, incomplete_groups)
