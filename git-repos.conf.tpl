# coding=utf-8

ignore_error = False

git_user_name = 'riag'

git_user_email = 'riag@163.com'

with_full_git_log = False

git_commit_msg = 'move from local Gogs'

# 一个 repo 移到 另一个 repo，目前暂不处理 submodule
# key 为 src repo
# value 为 map，map['dest'] = dest repo
one_repo_map = {
	'<src repo url>': {
		'dest': '<dest repo url>',
		'with-submodules': True
	},
}

