# **Z_Lib 開発計画書**

## **1\. 概要**

Z_Lib は、Pythonにおいて標準ファイルシステム（ローカルファイル）とZIPアーカイブ内のファイルを、パス文字列の記述だけで完全に透過的かつシームレスに扱うためのラッパーライブラリである。

既存の os や shutil と同等のインターフェースを提供することで、既存コードからの移行コストを最小限に抑えつつ、ZIPファイルの構造的制約（都度展開・再圧縮によるパフォーマンス低下）を状態管理によって解決することを目的とする。

## **2\. コア・コンセプト**

1. **透過的インターフェース（標準ライブラリモ倣型）**  
   Z_Lib は内部に os や shutil という名前空間を持ち、標準ライブラリと極力同じシグネチャ（引数と戻り値）でメソッドを提供する。
   - 例: z_lib.os.listdir("a/b.zip/c")
   - 例: z_lib.shutil.copy2("src.txt", "a/b.zip/dst.txt")
2. **明示的な状態管理（ロード/アンロード制約）**  
   ZIPファイルの「都度開閉による極端なパフォーマンス低下」や「意図しないZIPの作成・破壊」を防ぐため、**事前に明示的にロード（マウント）されたZIPファイルに対してのみ操作を許可**する。  
   未ロードのZIPパスに対して操作（作成・コピー・削除など）が行われた場合は、即座に例外（ZipNotLoadedError）を送出する。
3. **宣言的な状態同期**  
   大量のZIPファイルを安全に扱うため、現在のロード状態と目標とするロード状態の差分を自動計算し、適切にファイルハンドルを開閉する swap_zip メソッドを提供する。

## **3\. クラス・メソッド設計**

### **3.1 本体クラス: Z_Lib**

状態管理（ZIPファイルのオープン・クローズ）と、パスの解釈を担う。

- **プロパティ（内部クラス）**
  - os: ファイルやディレクトリの基本操作を提供する名前空間。
  - shutil: 高度なファイル操作（コピーやツリー削除など）を提供する名前空間。
- **属性**
  - \_loaded_zips (dict): 現在ロードされているZIPファイルの正規化パスをキーとし、ファイルオブジェクト（fs.zipfs.ZipFS などを想定）を値とする辞書。
- **メソッド**
  - load_zip(load_list: list, create: bool \= False) \-\> None  
    指定されたZIPファイルをマウントし、操作可能な状態にする。create=True の場合、ファイルが存在しなければ新規作成の準備を行う。
  - unload_zip(unload_list: list) \-\> None  
    指定されたZIPファイルをアンマウントし、変更内容をディスクに書き込んで（保存して）閉じる。
  - swap_zip(target_zips: list, create: bool \= False) \-\> None  
    現在のロード状態を target_zips の状態と完全に同期させる（差分のみをロード/アンロードする）。空リストを渡すと全アンロード。
  - \_split_zip_path(path: str) \-\> tuple\[str|None, str\]  
    パス文字列を受け取り、.zip/ のセパレータで分割する。ZIPのパスと内部パスのタプルを返す。含まれない場合は (None, path)。

### **3.2 内部クラス: Z_OS**

Z_Lib.os として公開される。標準の os モジュールの機能を透過的にラップする。

- **プロパティ（内部クラス）**
  - path: パス操作・判定を提供する名前空間（Z_OS_Path）。
- **メソッド（例）**
  - listdir(path: str) \-\> list
  - mkdir(path: str) \-\> None
  - remove(path: str) \-\> None
  - walk(top: str) \-\> generator
    - ※ロード中のZIPに遭遇した場合は、その中身もディレクトリツリーとして展開して返す特別な挙動を実装する。

### **3.3 内部クラス: Z_OS_Path**

Z_Lib.os.path として公開される。標準の os.path モジュールの機能を透過的にラップする。

- **メソッド（例）**
  - exists(path: str) \-\> bool
  - isfile(path: str) \-\> bool
  - isdir(path: str) \-\> bool
  - join(\*paths: str) \-\> str

### **3.4 内部クラス: Z_Shutil**

Z_Lib.shutil として公開される。標準の shutil モジュールの機能を透過的にラップする。

- **メソッド（例）**
  - copy2(src: str, dst: str) \-\> str
  - move(src: str, dst: str) \-\> str

## **4\. エラーハンドリング（例外）**

- ZipNotLoadedError (Exception)
  - **発生条件**: ロードされていないZIPファイルの内部パスに対して、書き込みや読み込みなどの操作を試みた場合。
  - **目的**: 意図しないファイル操作や、都度開閉によるパフォーマンス劣化を開発者に警告し、明示的な load_zip または swap_zip を促す。

## **5\. バックエンド実装方針（想定）**

実際のZIPファイルへのI/O処理は、標準の zipfile モジュールではなく、サードパーティ製ライブラリである **pyfilesystem2 (fs.zipfs.ZipFS)** の利用を強く推奨する。

これにより、ZIP内部の「ディレクトリの作成 (makedir)」や「ファイルの削除 (remove)」など、標準ライブラリでは困難なインプレース風の操作を、ラッパー側で再実装する手間を省き、堅牢な処理を実現できる。

## **6\. ユースケース（想定フロー）**

z_lib \= Z_Lib()

\# 1\. 処理対象のZIPを宣言的にロード (存在しない場合は新規作成準備)  
z_lib.swap_zip(\["a/a.zip", "a/b.zip"\], create=True)

\# 2\. 透過的なファイル操作  
if not z_lib.os.path.exists("a/a.zip/logs/"):  
 z_lib.os.mkdir("a/a.zip/logs/")

z_lib.shutil.copy2("local_error.log", "a/a.zip/logs/error.log")

\# 3\. エラーチェック (未ロードのZIPへの操作は安全に弾かれる)  
try:  
 z_lib.shutil.copy2("local_error.log", "a/c.zip/logs/error.log")  
except ZipNotLoadedError:  
 print("安全にブロックされました")

\# 4\. 別の処理へ移行 (a.zip, b.zip は自動保存され、c.zip が開く)  
z_lib.swap_zip(\["a/c.zip"\], create=True)

\# 5\. 処理完了、全て安全にクローズ  
z_lib.swap_zip(\[\])
