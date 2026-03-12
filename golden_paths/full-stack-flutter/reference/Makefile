.PHONY: help install dev build lint typecheck mobile-dev mobile-ios mobile-android mobile-build-ios mobile-build-android mobile-codegen

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-25s\033[0m %s\n", $$1, $$2}'

install: ## Install all dependencies (web + Flutter)
	pnpm install
	cd apps/mobile && flutter pub get

dev: ## Start web app in development mode
	pnpm dev

build: ## Build web app for production
	pnpm build

lint: ## Lint all web/packages code
	pnpm lint

typecheck: ## Type-check all web/packages code
	pnpm typecheck

mobile-dev: ## Start Flutter app (choose device interactively)
	cd apps/mobile && flutter run --dart-define-from-file=.env.json

mobile-ios: ## Run Flutter app on iOS simulator
	cd apps/mobile && flutter run -d "iPhone 16" --dart-define-from-file=.env.json

mobile-android: ## Run Flutter app on Android emulator
	cd apps/mobile && flutter run -d emulator --dart-define-from-file=.env.json

mobile-build-ios: ## Build Flutter iOS release (requires Xcode)
	cd apps/mobile && flutter build ios --dart-define-from-file=.env.json

mobile-build-android: ## Build Flutter Android APK
	cd apps/mobile && flutter build apk --dart-define-from-file=.env.json

mobile-codegen: ## Run Dart build_runner (Riverpod + Freezed code generation)
	cd apps/mobile && dart run build_runner build --delete-conflicting-outputs

mobile-codegen-watch: ## Watch for changes and run Dart build_runner
	cd apps/mobile && dart run build_runner watch --delete-conflicting-outputs

mobile-test: ## Run Flutter tests
	cd apps/mobile && flutter test

mobile-lint: ## Run Flutter/Dart analysis
	cd apps/mobile && dart analyze
