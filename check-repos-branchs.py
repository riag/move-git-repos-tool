# coding=utf-8

import os
import subprocess
import re

import click

import pybee

#　当前路径
curr_path=os.path.abspath(os.getcwd())
# 脚本所在路径
script_path=os.path.abspath(os.path.dirname(__file__))

ssh_git_repo_pattern = re.compile('(\S+)@(\S+)/(\S+).git')

class Context(object):
    def __init__(self, config):
        self.config = config
        self.work_dir = ''
        self.origin_repos_dir = ''

        self.repos = []

def git_pull(fpath):
    cmd = 'git pull'
    subprocess.run(
            cmd, cwd=fpath, shell=True
            )

def get_repo_name(repo_url):
    t = ssh_git_repo_pattern.match(repo_url)
    if t: return t.group(3)
    return None

def git_clone(fpath, repo):
    gitdir = os.path.join(fpath, '.git')
    if os.path.isdir(fpath) and os.path.isdir(gitdir):
        git_pull(fpath)
    else:
        cmd = 'git clone %s %s' % (repo, fpath)
        subprocess.run(cmd, shell=True) 

def git_branches(fpath):
    cmd = 'git branch -r'
    t = pybee.shell.call(cmd, cwd=fpath, shell=True)
    tt = t.split('\n')
    branches = []
    for l in tt:
        if not l: continue
        l = l.strip()
        if not l: continue
        if l.startswith('origin/HEAD'): continue
        l = l.strip('origin/')
        branches.append(l)

    return branches
        

def load_config(config_file):
    module = pybee.importutil.import_module_from_src(
            'git-repos-config', config_file
            )
    return module

def create_context(config):

    context = Context(config)
    context.config = config
    context.work_dir = os.path.join(curr_path, 'work-repos')
    context.origin_repos_dir = os.path.join(context.work_dir, 'origin-repos')

    context.repos.extend(config.one_repo_map.keys())
    for dest_url, m in config.multi_repo_map.items():
        for name, url in m.items():
            if not url: continue
            context.repos.append(url)

    return context

def prepare(context):
    pybee.path.mkdir(context.work_dir)
    pybee.path.mkdir(context.origin_repos_dir)

def check_repo(context, repo_url):
    repo_name = get_repo_name(repo_url)
    fpath = os.path.join(context.origin_repos_dir, repo_name)
    git_clone(fpath, repo_url)

    branches = git_branches(fpath)
    if len(branches) <= 1: return

    print('repo %s has follow branch:' % repo_url)
    for b in branches:
        print('\t%s' % b)

def check_repos_branchs(context):
    for repo in context.repos:
        print(repo)
        check_repo(context, repo)

@click.command()
@click.option('-c','--config', 'config_file', default='git-repos.conf')
def main(config_file):
    
    config = load_config(config_file)

    context = create_context(config)

    prepare(context)

    check_repos_branchs(context)


if __name__ == '__main__':
    main()
