# OpenShift Demo

OpenShift Localのクイック作成をテストするコード。

## クイック作成テスト手順（Webコンソール / Dockerfile）

以下は OpenShift Web コンソールの `Gitからのインポート` を使った検証手順です。

### 1. Git リポジトリを用意

`Dockerfile` 戦略を使うため、少なくとも次を含めます。

- `Dockerfile`
- `app.py`
- `requirements.txt`
- `templates/index.html`

### 2. Web コンソールでインポート

1. `+Add` -> `Git Repository`（Gitからのインポート）を開く
2. `Git Repo URL` に対象リポジトリ URL を入力
3. Import Strategy は `Dockerfile` を選択
4. Project は `todo-demo` を選択（なければ作成）
5. `Create` を実行

### 3. PostgreSQL を作成

アプリは DB を必要とするため、`todo-demo` に PostgreSQL リソースを適用します。
namespaceは上記で指定したProjectを設定。

```bash
oc apply -n todo-demo -f openshift/01-secret.yaml
oc apply -n todo-demo -f openshift/02-postgres-pvc.yaml
oc apply -n todo-demo -f openshift/03-postgres-deployment.yaml
oc apply -n todo-demo -f openshift/04-postgres-service.yaml
oc rollout status deployment/postgres -n todo-demo
```

### 4. アプリの接続先を PostgreSQL に切り替え
PostgreSQLユーザー、パスワードは01-secret.yamlを変更

```bash
oc set env deployment/openshift-quick-create-demo \
  -n todo-demo \
  DATABASE_URL='postgresql+psycopg2://todo:todo-pass-123@postgres:5432/tododb'
oc rollout status deployment/openshift-quick-create-demo -n todo-demo
```

### 5. 動作確認

```bash
ROUTE_HOST="$(oc get route openshift-quick-create-demo -n todo-demo -o jsonpath='{.spec.host}')"
curl -k "https://${ROUTE_HOST}/healthz"
curl -k "https://${ROUTE_HOST}/todos"
```

期待値:

- `/healthz` が `{"status":"ok"}`
- `/todos` が `[]` または Todo 一覧 JSON

