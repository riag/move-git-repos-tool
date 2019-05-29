# coding=utf-8

import click
import os
import subprocess
import io
import sys
import re

import pybee

#　当前路径
curr_path=os.path.abspath(os.getcwd())
# 脚本所在路径
script_path=os.path.abspath(os.path.dirname(__file__))

ssh_git_repo_pattern = re.compile('(\S+)@(\S+)/(\S+).git')

class GitRepoContext(object):
    def __init__(self, config):
        self.config = config
        self.result = {}
        self.action_list = []
        self.work_dir = ''
        self.origin_repos_dir = ''
        self.new_repos_dir = ''

        self.dry_run = False

class BaseMoveAction(object):
    def __init__(self, context, key, info):
        self.context = context
        self.key = key
        self.info = info

    def git_clone(self, fpath, repo):
        gitdir = os.path.join(fpath, '.git')
        if os.path.isdir(fpath) and os.path.isdir(gitdir):
            self.git_pull(fpath)
        else:
            cmd = 'git clone %s %s' % (repo, fpath)
            subprocess.run(cmd, cwd=self.context.work_dir, shell=True) 

    def git_clone_with_all_branches(self. fpath, repo):
        '''
        clone repo, 包括所有分支

        checkout 其中一个分支
        git checkout --track origin/develop
        '''
        pass

    def git_submodule_update(self, fpath):

        cmd = 'git submodule init'
        subprocess.run(
                cmd, cwd=fpath, shell=True
                )
        cmd = 'git submodule update'
        subprocess.run(
                cmd, cwd=fpath, shell=True
                )

    def git_pull(self, fpath):
        cmd = 'git pull'
        subprocess.run(
                cmd, cwd=fpath, shell=True
                )

    def set_git_user_info(self, fpath, user_name, user_email):
        cmd = 'git config user.name %s' % user_name
        subprocess.run(
                cmd, cwd=fpath, shell=True
                )

        cmd = 'git config user.email %s' % user_email
        subprocess.run(
                cmd, cwd=fpath, shell=True
                )

    def set_git_repo_remote_url(self, fpath, new_repo):
        cmd = 'git remote set-url origin %s' % new_repo
        subprocess.run(
                cmd, cwd=fpath, shell=True
                )
    def git_push(self, fpath):
        if self.context.dry_run:
            print('in dry run mode, so ignore git push')
            return

        cmd = 'git push'
        subprocess.run(cmd, cwd=fpath, shell=True)

    def git_push_all(self, fpath):
        if self.context.dry_run:
            print('in dry run mode, so ignore git push')
            return

        cmd = 'git push origin --all'
        subprocess.run(cmd, cwd=fpath, shell=True)

    def git_commit(self, fpath, msg):
        cmd = "git commit -m '%s' " % msg
        subprocess.run(cmd, cwd=fpath, shell=True)

    def add_all_to_git_repo(self, fpath):
        cmd = 'git add -f .'
        subprocess.run(cmd, cwd=fpath, shell=True)

    def parse_repo_url(self, repo_url):
        t = ssh_git_repo_pattern.match(repo_url)
        return t

    def get_repo_name(self, repo_url):
        t = self.parse_repo_url(repo_url)
        if t: return t.group(3)
        return None

    def run(self):
        pass

def copy_ignore_git_dir(src, names):
    return ['.git']

def copy_ignore_git_dir_and_ignore(src, names):
    return ['.git', '.gitignore']

class MoveOneRepoAction(BaseMoveAction):
    def __init__(self, context, src, dest):
        info = 'move repo from %s to %s' % (src, dest)
        super().__init__(context, src, info)

        self.with_submodules = False

        self.src_url = src
        self.dest_url = dest

        self.origin_repo_name = self.get_repo_name(
                self.src_url
                )
        self.new_repo_name = self.get_repo_name(
                self.dest_url
                )
    
    def run(self):
        origin_repos_dir = self.context.origin_repos_dir
        new_repos_dir = self.context.new_repos_dir

        origin_repo_path = os.path.join(origin_repos_dir, self.origin_repo_name)
        self.git_clone(origin_repo_path, self.src_url)

        if self.with_submodules:
            self.git_submodule_update(origin_repo_path)

        new_repo_path = os.path.join(new_repos_dir, self.new_repo_name)
        self.git_clone(new_repo_path, self.dest_url)

        # 直接在旧版的 repo 提交
        if self.context.config.with_full_git_log:
            self.set_git_repo_remote_url(origin_repo_path, self.dest_url)
            self.git_push_all(origin_repo_path)

            pybee.path.rmtree(origin_repo_path)
            self.git_pull(new_repo_path)
        else:
            pybee.path.copytree(
                    origin_repo_path, new_repo_path,
                    ignore=copy_ignore_git_dir)
            self.add_all_to_git_repo(new_repo_path)
            self.git_commit(new_repo_path, 
                    self.context.config.git_commit_msg
                    )
            self.git_push(new_repo_path)

        self.context.result[self.key] = 'ok'


class MergeMultiReposAction(BaseMoveAction):
    def __init__(self, context, src, dest, sub_dir_repo_map):
        info = 'merge multi repos to %s' % dest
        super().__init__(context, dest, info)
        
        self.src_url = src
        self.dest_url = dest
        self.sub_dir_repo_map = sub_dir_repo_map

        self.origin_repo_name = ''
        if self.src_url:
            self.origin_repo_name = self.get_repo_name(
                self.src_url
                )
        self.new_repo_name = self.get_repo_name(
                self.dest_url
                )
    def merge_repo(self, dest_dir, sub_dir, src_url):
        origin_repos_dir = self.context.origin_repos_dir

        repo_name = self.get_repo_name(src_url)

        origin_repo_path = os.path.join(origin_repos_dir, repo_name)
        self.git_clone(origin_repo_path, src_url)

        d = os.path.join(dest_dir, sub_dir)

        pybee.path.copytree(
                origin_repo_path, d,
                ignore=copy_ignore_git_dir_and_ignore)

    def run(self):

        origin_repos_dir = self.context.origin_repos_dir
        new_repos_dir = self.context.new_repos_dir

        new_repo_path = os.path.join(new_repos_dir, self.new_repo_name)
        self.git_clone(new_repo_path, self.dest_url)

        if self.src_url:
            origin_repo_path = os.path.join(origin_repos_dir, self.origin_repo_name)
            self.git_clone(origin_repo_path, self.src_url)

            pybee.path.copytree(
                    origin_repo_path, new_repo_path,
                    ignore=copy_ignore_git_dir)

        for sub_dir, repo_url in self.sub_dir_repo_map.items():
            self.merge_repo(new_repo_path, sub_dir, repo_url)

        self.add_all_to_git_repo(new_repo_path)
        self.git_commit(new_repo_path, 
                self.context.config.git_commit_msg
                )
        self.git_push(new_repo_path)
        self.context.result[self.key] = 'ok'

def load_config(config_file):
    module = pybee.importutil.import_module_from_src(
            'git-repos-config', config_file
            )
    return module

def create_context(config, dry_run):
    context = GitRepoContext(config)
    context.work_dir = os.path.join(curr_path, 'work-repos')
    context.origin_repos_dir = os.path.join(context.work_dir, 'origin-repos')
    context.new_repos_dir = os.path.join(context.work_dir, 'new-repos')

    context.dry_run = dry_run

    for origin_url, m in config.one_repo_map.items():
        with_submodules = False
        if type(m) is str:
            dest_repo = m
        else:
            dest_repo = m['dest']
            with_submodules = m.get('with-submodules', with_submodules)
        action = MoveOneRepoAction(context, origin_url, dest_repo)
        action.with_submodules = with_submodules

        context.action_list.append(action)

    for dest_url, m in config.multi_repo_map.items():
        src_url = m.pop('__src', None)
        action = MergeMultiReposAction(
                context, src_url, dest_url, m
                )

        context.action_list.append(action)

    return context


def prepare(context):

    pybee.path.mkdir(context.work_dir)
    pybee.path.mkdir(context.origin_repos_dir)
    pybee.path.mkdir(context.new_repos_dir)


def run_actions(context):
    for action in context.action_list:
        try:
            print('')
            print('===============')
            print(action.info)
            action.run()
        except:
            print("%s failed" % action.info)
            print(sys.exc_info()[0])
            if not context.config.ignore_error:
                raise 

            continue
        finally:
            print('===============')

@click.command()
@click.option('-c','--config', 'config_file', default='git-repos.conf')
@click.option('--dry-run', 'dry_run', is_flag=True, default=False)
def main(config_file, dry_run):

    config = load_config(config_file)

    context = create_context(config, dry_run)

    prepare(context)

    run_actions(context)

if __name__ == '__main__':
    main()
