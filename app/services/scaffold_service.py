import base64
import requests
from app.config import Config

# Minimal, locked-in starter files per supported tech stack. Each entry is a
# single-source-of-truth description of what a brand-new project in that
# stack needs to be clonable and runnable -- nothing extra, no opinionated
# tooling beyond the essentials.
SCAFFOLDS = {
    'flask': {
        'label': 'Python / Flask',
        'gitignore': "__pycache__/\n*.pyc\n.venv/\nenv/\ninstance/\n.env\n",
        'files': {
            'requirements.txt': "flask\npython-dotenv\n",
            'app.py': (
                "from flask import Flask\n\n"
                "app = Flask(__name__)\n\n\n"
                "@app.route('/')\n"
                "def index():\n"
                "    return 'Hello from {title}!'\n\n\n"
                "if __name__ == '__main__':\n"
                "    app.run(debug=True)\n"
            ),
        },
    },
    'react': {
        'label': 'React',
        'gitignore': "node_modules/\ndist/\n.env\n",
        'files': {
            'package.json': (
                '{{\n'
                '  "name": "{slug}",\n'
                '  "private": true,\n'
                '  "version": "0.1.0",\n'
                '  "scripts": {{\n'
                '    "dev": "vite",\n'
                '    "build": "vite build"\n'
                '  }},\n'
                '  "dependencies": {{\n'
                '    "react": "^18.2.0",\n'
                '    "react-dom": "^18.2.0"\n'
                '  }},\n'
                '  "devDependencies": {{\n'
                '    "vite": "^5.0.0"\n'
                '  }}\n'
                '}}\n'
            ),
            'src/App.jsx': (
                "export default function App() {{\n"
                "  return <h1>{title}</h1>;\n"
                "}}\n"
            ),
        },
    },
    'node': {
        'label': 'Node.js',
        'gitignore': "node_modules/\n.env\n",
        'files': {
            'package.json': (
                '{{\n'
                '  "name": "{slug}",\n'
                '  "private": true,\n'
                '  "version": "0.1.0",\n'
                '  "main": "index.js",\n'
                '  "scripts": {{\n'
                '    "start": "node index.js"\n'
                '  }}\n'
                '}}\n'
            ),
            'index.js': "console.log('Hello from {title}!');\n",
        },
    },
    'flutter': {
        'label': 'Flutter',
        'gitignore': ".dart_tool/\n.packages\nbuild/\n",
        'files': {
            'pubspec.yaml': (
                "name: {slug}\n"
                "description: {title}\n"
                "environment:\n"
                "  sdk: '>=3.0.0 <4.0.0'\n"
            ),
            'lib/main.dart': (
                "void main() {{\n"
                "  print('Hello from {title}!');\n"
                "}}\n"
            ),
        },
    },
}

GITHUB_API_BASE_URL = Config.GITHUB_API_BASE_URL


def get_supported_stacks():
    return [(key, meta['label']) for key, meta in SCAFFOLDS.items()]


def _slugify(title):
    slug = ''.join(c.lower() if c.isalnum() else '-' for c in title).strip('-')
    while '--' in slug:
        slug = slug.replace('--', '-')
    return slug or 'devrank-project'


def _headers(token):
    return {
        'Authorization': f'Bearer {token}',
        'Accept': 'application/vnd.github+json',
        'X-GitHub-Api-Version': '2022-11-28',
    }


def _create_repo(token, repo_name, description):
    response = requests.post(
        f'{GITHUB_API_BASE_URL}/user/repos',
        headers=_headers(token),
        json={
            'name': repo_name,
            'description': description[:350],
            'private': False,
            'auto_init': True,  # creates an initial commit on main so Contents API has a base to write onto
        },
    )
    response.raise_for_status()
    return response.json()


def _put_file(token, owner, repo_name, path, content, message):
    response = requests.put(
        f'{GITHUB_API_BASE_URL}/repos/{owner}/{repo_name}/contents/{path}',
        headers=_headers(token),
        json={
            'message': message,
            'content': base64.b64encode(content.encode('utf-8')).decode('ascii'),
        },
    )
    response.raise_for_status()
    return response.json()


class ScaffoldError(Exception):
    pass


def scaffold_project_to_github(token, github_username, project):
    """Create a new GitHub repo for `project` and push the minimal starter
    files for its tech_stack. Returns the repo's HTML URL on success.
    Raises ScaffoldError on any failure (repo name clash, bad token, etc.)."""

    stack = SCAFFOLDS.get(project.tech_stack)
    if not stack:
        raise ScaffoldError(f'Unsupported tech stack: {project.tech_stack}')

    slug = _slugify(project.title)

    try:
        repo = _create_repo(token, slug, project.description)
    except requests.HTTPError as e:
        if e.response is not None and e.response.status_code == 422:
            raise ScaffoldError(
                f'A GitHub repo named "{slug}" already exists on your account.'
            ) from e
        raise ScaffoldError('Could not create the GitHub repo.') from e

    repo_name = repo['name']
    owner = repo['owner']['login']

    format_kwargs = {'title': project.title, 'slug': slug}
    files_to_push = dict(stack['files'])
    files_to_push['.gitignore'] = stack['gitignore']
    files_to_push['README.md'] = (
        f"# {project.title}\n\n{project.description}\n\n"
        f"Scaffolded from DevRank ({stack['label']}).\n"
    )

    try:
        for path, template in files_to_push.items():
            _put_file(
                token, owner, repo_name, path,
                template.format(**format_kwargs),
                message=f'Scaffold: add {path}',
            )
    except requests.HTTPError as e:
        raise ScaffoldError('Repo was created but scaffold files failed to push.') from e

    return repo['html_url']
