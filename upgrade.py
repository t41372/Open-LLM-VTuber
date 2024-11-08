#!/usr/bin/env python3
import os
import shutil
from datetime import datetime
import subprocess
import sys
import locale
from colorama import init, Fore, Style

# Initialize colorama for cross-platform color support
init()

# 语言字典 / Language dictionary
TEXTS = {
    'zh': {
        'welcome_message': 'Auto-Upgrade Script v.0.1.0\nOpen-LLM-VTuber 升级脚本 - 此脚本仍在实验阶段，可能无法按预期工作。',
        'lang_select': '请选择语言/Please select language (zh/en):',
        'invalid_lang': '无效的语言选择，使用英文作为默认语言',
        'not_git_repo': '错误：当前目录不是git仓库。请进入 Open-LLM-VTuber 目录后再运行此脚本。\n当然，更有可能的是你下载的Open-LLM-VTuber不包含.git文件夹 (如果你是透过下载压缩包而非使用 git clone 命令下载的话可能会造成这种情况)，这种情况下目前无法用脚本升级。',
        'backup_config': '备份配置文件到: {}',
        'no_config': '警告：未找到conf.yaml文件',
        'uncommitted': '发现未提交的更改，正在暂存...',
        'stash_error': '错误：无法暂存更改',
        'changes_stashed': '更改已暂存',
        'pulling': '正在从远程仓库拉取更新...',
        'pull_error': '错误：无法拉取更新',
        'restoring': '正在恢复暂存的更改...',
        'conflict_warning': '警告：恢复暂存的更改时发生冲突',
        'manual_resolve': '请手动解决冲突',
        'stash_list': "你可以使用 'git stash list' 查看暂存的更改",
        'stash_pop': "使用 'git stash pop' 恢复更改",
        'upgrade_complete': '升级完成！',
        'check_config': '1. 请检查conf.yaml是否需要更新',
        'resolve_conflicts': '2. 如果有配置文件冲突，请手动解决',
        'check_backup': '3. 检查备份的配置文件以确保没有丢失重要设置',
        'git_not_found': '错误：未检测到 Git。请先安装 Git:\nWindows: https://git-scm.com/download/win\nmacOS: brew install git\nLinux: sudo apt install git',
        'operation_preview': '''
此脚本将执行以下操作：
1. 备份当前的 conf.yaml 配置文件
2. 暂存所有未提交的更改 (git stash)
3. 从远程仓库拉取最新代码 (git pull)
4. 尝试恢复之前暂存的更改 (git stash pop)

是否继续？(y/n): ''',
        'abort_upgrade': '升级已取消',
    },
    'en': {
        'welcome_message': 'Auto-Upgrade Script v.0.1.0\nOpen-LLM-VTuber upgrade script - This script is highly experimental and may not work as expected.',
        'lang_select': '请选择语言/Please select language (zh/en):',
        'invalid_lang': 'Invalid language selection, using English as default',
        'not_git_repo': 'Error: Current directory is not a git repository. Please run this script inside the Open-LLM-VTuber directory.\nAlternatively, it is likely that the Open-LLM-VTuber you downloaded does not contain the .git folder (this can happen if you downloaded a zip archive instead of using git clone), in which case you cannot upgrade using this script.',
        'backup_config': 'Backing up config file to: {}',
        'no_config': 'Warning: conf.yaml not found',
        'uncommitted': 'Found uncommitted changes, stashing...',
        'stash_error': 'Error: Unable to stash changes',
        'changes_stashed': 'Changes stashed',
        'pulling': 'Pulling updates from remote repository...',
        'pull_error': 'Error: Unable to pull updates',
        'restoring': 'Restoring stashed changes...',
        'conflict_warning': 'Warning: Conflicts occurred while restoring stashed changes',
        'manual_resolve': 'Please resolve conflicts manually',
        'stash_list': "Use 'git stash list' to view stashed changes",
        'stash_pop': "Use 'git stash pop' to restore changes",
        'upgrade_complete': 'Upgrade complete!',
        'check_config': '1. Please check if conf.yaml needs updating',
        'resolve_conflicts': '2. Resolve any config file conflicts manually',
        'check_backup': '3. Check backup config to ensure no important settings are lost',
        'git_not_found': 'Error: Git not found. Please install Git first:\nWindows: https://git-scm.com/download/win\nmacOS: brew install git\nLinux: sudo apt install git',
        'operation_preview': '''
This script will perform the following operations:
1. Backup current conf.yaml configuration file
2. Stash all uncommitted changes (git stash)
3. Pull latest code from remote repository (git pull)
4. Attempt to restore previously stashed changes (git stash pop)

Continue? (y/n): ''',
        'abort_upgrade': 'Upgrade aborted',
    }
}

def get_system_language():
    """获取系统语言/Get system language"""
    try:
        sys_lang = locale.getdefaultlocale()[0]
        return 'zh' if sys_lang.startswith('zh') else 'en'
    except:
        return 'en'

def select_language():
    """选择语言/Select language"""
    default_lang = get_system_language()
    try:
        lang = input(TEXTS['en']['lang_select'] + ' ').lower()
        return lang if lang in ['zh', 'en'] else default_lang
    except:
        return default_lang

def run_command(command):
    """运行shell命令并返回结果/Run shell command and return result"""
    try:
        result = subprocess.run(command, shell=True, check=True, 
                              capture_output=True, text=True)
        return True, result.stdout
    except subprocess.CalledProcessError as e:
        return False, e.stderr

def backup_config():
    """备份conf.yaml文件/Backup conf.yaml file"""
    backup_path = 'conf.yaml.backup'
    
    if os.path.exists('conf.yaml'):
        print(Fore.GREEN + texts['backup_config'].format(backup_path) + Style.RESET_ALL)
        shutil.copy2('conf.yaml', backup_path)
        return True
    return False

def check_git_installed():
    """检查是否安装了Git/Check if Git is installed"""
    command = 'where git' if sys.platform == 'win32' else 'which git'
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True)
        return result.returncode == 0
    except:
        return False

def main():
    global texts
    print(Fore.CYAN + TEXTS['en']['welcome_message'] + Style.RESET_ALL)
    
    lang = select_language()
    texts = TEXTS[lang]

    # 检查Git是否已安装/Check if Git is installed
    if not check_git_installed():
        print(Fore.RED + texts['git_not_found'] + Style.RESET_ALL)
        sys.exit(1)

    # 显示操作预览并请求确认
    response = input(Fore.YELLOW + texts['operation_preview'] + Style.RESET_ALL).lower()
    if response != 'y':
        print(Fore.YELLOW + texts['abort_upgrade'] + Style.RESET_ALL)
        sys.exit(0)

    # 检查是否在git仓库中/Check if in git repository
    success, _ = run_command('git rev-parse --is-inside-work-tree')
    if not success:
        print(Fore.RED + texts['not_git_repo'] + Style.RESET_ALL)
        sys.exit(1)

    # 检查是否有未提交的更改/Check for uncommitted changes
    success, changes = run_command('git status --porcelain')
    has_changes = bool(changes.strip())

    # 备份配置文件/Backup config file
    if not backup_config():
        print(Fore.YELLOW + texts['no_config'] + Style.RESET_ALL)
    
    if has_changes:
        print(Fore.YELLOW + texts['uncommitted'] + Style.RESET_ALL)
        success, output = run_command('git stash')
        if not success:
            print(Fore.RED + texts['stash_error'] + Style.RESET_ALL)
            sys.exit(1)
        print(Fore.GREEN + texts['changes_stashed'] + Style.RESET_ALL)

    # 更新代码/Update code
    print(Fore.CYAN + texts['pulling'] + Style.RESET_ALL)
    success, output = run_command('git pull')
    if not success:
        print(Fore.RED + texts['pull_error'] + Style.RESET_ALL)
        if has_changes:
            print(Fore.YELLOW + texts['restoring'] + Style.RESET_ALL)
            run_command('git stash pop')
        sys.exit(1)

    # 恢复暂存的更改/Restore stashed changes
    if has_changes:
        print(Fore.YELLOW + texts['restoring'] + Style.RESET_ALL)
        success, output = run_command('git stash pop')
        if not success:
            print(Fore.RED + texts['conflict_warning'] + Style.RESET_ALL)
            print(Fore.YELLOW + texts['manual_resolve'] + Style.RESET_ALL)
            print(Fore.CYAN + texts['stash_list'] + Style.RESET_ALL)
            print(Fore.CYAN + texts['stash_pop'] + Style.RESET_ALL)
            sys.exit(1)

    print(Fore.GREEN + "\n" + texts['upgrade_complete'] + Style.RESET_ALL)
    print(Fore.CYAN + texts['check_config'] + Style.RESET_ALL)
    print(Fore.CYAN + texts['resolve_conflicts'] + Style.RESET_ALL)
    print(Fore.CYAN + texts['check_backup'] + Style.RESET_ALL)

if __name__ == "__main__":
    main()