# Checkmark

A simple command-line tool to check the progress of tasks in a Markdown checklist. It scans a `.md` file for checklist items (of the form `- [ ]` and `- [x]`) and displays a progress bar.

## Features

- Identifies completed (`- [x]`) and pending (`- [ ]`) tasks in a Markdown file.
- Calculates the number of tasks done vs. total tasks.
- Optionally displays the title from the first `# Heading` in the file.
- Shows a handy progress bar with completion percentage.

## Installation

1. Make sure you have Python 3.7+ installed.
2. Clone or download this repository.
3. (Optional) Install dependencies in a virtual environment if desired.

There are no additional external dependencies besides Python's standard library.

## Usage

```bash
python checkmark.py /path/to/your_checklist.md
```

## Example

Suppose you have a file named todo.md with the following content:
```markdown
# My Todo List

- [ ] Buy groceries
- [x] Write blog post
- [ ] Go running
```

Running python checkmark.py todo.md will produce output like:
```
📊 Progress for:
My Todo List
[█-------] 1/3 tasks completed (33.3%)
```

## Contributing

Feel free to submit issues or pull requests. This is a small tool, so contributions are always welcome.

## License
This project is licensed under the MIT License. See the [LICENSE](./LICENSE) file for details.
