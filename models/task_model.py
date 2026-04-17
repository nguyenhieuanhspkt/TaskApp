class Task:
    def __init__(self, id, title, folder, status="doing", start_date=None, due_date=None, content="", author="", created_at=None):
        self.id = id
        self.title = title
        self.folder = folder
        self.status = status
        self.start_date = start_date
        self.due_date = due_date
        self.content = content
        self.author = author
        self.created_at = created_at
        self.edited_at = None
