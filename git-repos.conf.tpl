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


# 多个 repo 合并成一个 repo, 目前这个还没实现
# key 为 dest repo
# value 为 map
# map 中 key 为子目录, value 为对应的 src repo
# map 中 __src  是对应的 src repo, 是在这个 repo 其中上合并其他 repo, 可以为空
multi_repo_map = {
	'<dest repo url>': {
		'__src': '<src repo url>',
		'<sub dir name>': '<merge repo url>',
		'<sub dir name>': '<merge repo url>'
	}
}
