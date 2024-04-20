from PyInstaller.utils.hooks import collect_submodules, collect_data_files

# Thu thập tất cả các submodule
hiddenimports = collect_submodules('currencies')

# Thu thập tất cả dữ liệu cần thiết (chẳng hạn như tệp dữ liệu hoặc tài nguyên khác)
datas = collect_data_files('currencies')