# Whispr - AI-Powered Audio Transcription & Enrichment Pipeline

**Whispr** is a self-contained AI system that transcribes audio recordings, enriches them with intelligent summaries, and generates beautifully formatted markdown documents with relevant images. Perfect for processing conference recordings, lectures, and presentations.

## 🎯 Current Status

### ✅ Completed Features

#### Core Pipeline
- **Audio Transcription**: GPU-accelerated Whisper large-v3 transcription
  - Supports multiple audio formats (m4a, mp3, wav, etc.)
  - Automatic language detection
  - Word-level timestamps support
  - **Performance**: ~70 seconds for 5-minute audio on RTX 4090 (15x faster than CPU)

- **LLM Summarization**: Self-contained vLLM with Qwen2.5-7B-Instruct-AWQ
  - Quantized model fits in 24GB VRAM (RTX 4090)
  - Generates structured summaries with sections, key points, glossary
  - Follow-up questions generation
  - **Model**: Qwen/Qwen2.5-7B-Instruct-AWQ (~5GB VRAM)

- **Understanding Level System**: Adaptive depth based on user knowledge
  - **Level 0**: Complete novice - extensive explanations, all terms defined
  - **Level 1**: Beginner - most terms defined, background context
  - **Level 2**: Basic understanding - specialized terms defined
  - **Level 3**: Intermediate - only niche terms defined
  - **Level 4**: Advanced - technical details, minimal explanations
  - **Level 5**: Expert - concise reference, no basic explanations

- **Image Processing**: Vision pipeline for uploaded images
  - Tesseract OCR for text extraction from slides/images
  - LLM-based image analysis (description, keywords, classification)
  - Intelligent image-to-section matching
  - Automatic placement in relevant document sections

- **Markdown Generation**: Clean, structured output
  - Overview section
  - Multiple content sections with key points
  - Glossary of technical terms
  - Follow-up questions
  - Embedded images with captions
  - Transcript links

#### Infrastructure
- **Self-Contained Docker Container**: Everything runs in one container
  - CUDA 12.4 + cuDNN runtime
  - PyTorch with CUDA support
  - vLLM server (starts automatically)
  - FastAPI worker service
  - Tesseract OCR
  - All dependencies bundled

- **GPU Acceleration**: Optimized for NVIDIA RTX 4090 (24GB VRAM)
  - Whisper: CUDA with float16 precision
  - vLLM: AWQ quantization for memory efficiency
  - Automatic device detection (CUDA/CPU fallback)

- **API Endpoints**:
  - `POST /process` - Process audio + optional images
  - `GET /health` - Health check
  - Supports multipart form uploads

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│              Whispr Self-Contained Container                 │
│                    (RTX 4090 Edition)                        │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐ │
│  │   Whisper    │    │     vLLM     │    │   Tesseract  │ │
│  │  large-v3    │    │ Qwen2.5-7B   │    │     OCR      │ │
│  │   (~4GB)     │    │   AWQ (~5GB) │    │              │ │
│  └──────┬───────┘    └──────┬───────┘    └──────┬───────┘ │
│         │                   │                   │          │
│         └───────────────────┼───────────────────┘          │
│                             │                              │
│                    ┌────────▼────────┐                     │
│                    │  FastAPI Worker │                     │
│                    │   (Port 9000)    │                     │
│                    └─────────────────┘                     │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### Processing Pipeline

1. **Audio Input** → Whisper transcription → Text segments
2. **Text** → vLLM summarization → Structured summary (sections, glossary, Q&A)
3. **Images (optional)** → OCR + LLM analysis → Image descriptions & keywords
4. **Image Matching** → LLM determines best section placement
5. **Markdown Generation** → Final enriched document

## 🚀 Quick Start

### Prerequisites
- NVIDIA GPU with 24GB+ VRAM (tested on RTX 4090)
- Docker with NVIDIA Container Toolkit
- CUDA 12.4+ drivers

### Build Container

```bash
cd worker
docker build -t whispr-worker:4090 .
```

### Run Container

```bash
docker run -d --gpus all \
  --name whispr \
  -p 9000:9000 \
  -v $(pwd)/artifacts:/app/artifacts \
  -v whispr-models:/app/models \
  whispr-worker:4090
```

**First startup takes ~2-3 minutes** (downloads Qwen2.5-7B-AWQ model)

### Test API

```bash
# Health check
curl http://localhost:9000/health

# Process audio with images
curl -X POST http://localhost:9000/process \
  -F "audio=@path/to/audio.m4a" \
  -F "images=@image1.jpg" \
  -F "images=@image2.jpg" \
  -F "title=My Presentation" \
  -F "understanding_level=2"
```

### Understanding Level Examples

```bash
# Complete novice (networking talk, no background)
-F "understanding_level=0"

# Beginner (some familiarity)
-F "understanding_level=1"

# Intermediate (working knowledge)
-F "understanding_level=3"

# Expert (quick reference)
-F "understanding_level=5"
```

## 📁 Project Structure

```
whispr/
├── server/              # Orchestration server (FastAPI)
│   ├── app.py          # Main API endpoints
│   ├── jobs.py         # Job registry
│   ├── pod_launcher.py # RunPod integration
│   └── runpod/         # RunPod abstraction layer
│
├── worker/             # Self-contained AI worker
│   ├── worker.py       # FastAPI service
│   ├── transcribe.py   # Whisper transcription
│   ├── summary.py      # LLM summarization prompts
│   ├── vision.py       # Image analysis (OCR + LLM)
│   ├── image_placement.py  # Image-to-section matching
│   ├── llm.py          # LLM client (vLLM/OpenAI-compatible)
│   ├── Dockerfile      # Container definition
│   └── docker/
│       └── entrypoint.sh  # Starts vLLM + worker
│
└── test-samples/       # Test audio files (OCP conference)
```

## 🔧 Configuration

### Environment Variables

```bash
# LLM Configuration
VLLM_MODEL=Qwen/Qwen2.5-7B-Instruct-AWQ
VLLM_GPU_MEMORY_UTILIZATION=0.50
LLM_BASE_URL=http://127.0.0.1:8000

# Worker Settings
PORT=9000
WHISPR_ARTIFACTS_ROOT=/app/artifacts
WHISPR_MODEL_CACHE_ROOT=/app/models

# Optional: Skip LLM for transcription-only testing
SKIP_LLM=false
```

## 📊 Performance

### RTX 4090 Benchmarks

| Task | Time | Notes |
|------|------|-------|
| Audio Transcription (5min) | ~70s | GPU-accelerated |
| LLM Summarization | ~10-15s | Depends on transcript length |
| Image Analysis (per image) | ~3-5s | OCR + LLM description |
| Full Pipeline (audio + 5 images) | ~2-3min | End-to-end |

### Memory Usage

- Whisper model: ~4GB VRAM
- vLLM (Qwen2.5-7B-AWQ): ~5GB VRAM
- KV Cache: ~2-3GB VRAM
- **Total**: ~11-12GB VRAM (leaves room for processing)

## 🧪 Testing

### Test Transcription Only

```bash
docker run --rm --gpus all \
  -v $(pwd)/test-samples:/app/test-samples:ro \
  whispr-worker:4090 \
  python3 -m worker.test_transcribe \
    /app/test-samples/Telemetry.m4a \
    --output-dir /app/artifacts/test
```

### Test Full Pipeline

```bash
# With audio only
curl -X POST http://localhost:9000/process \
  -F "audio=@test-samples/Redfish.m4a" \
  -F "title=OCP Redfish Talk" \
  -F "understanding_level=2"

# With audio + images
curl -X POST http://localhost:9000/process \
  -F "audio=@test-samples/Telemetry.m4a" \
  -F "images=@media/ocp/credo/IMG_0990.jpeg" \
  -F "images=@media/ocp/credo/IMG_0991.jpeg" \
  -F "title=OCP Telemetry Session" \
  -F "understanding_level=1"
```

## 🎯 Next Steps / Roadmap

### Immediate (Next Session)
- [ ] **Test image processing** with OCP conference photos
- [ ] **Verify image placement** logic works correctly
- [ ] **Enhance markdown output** with better image formatting
- [ ] **Add image confidence scores** to output

### Short Term
- [ ] **PDF/Slideshow Processing**: Extract slides from PDFs/PPTX
  - Use `pdf2image` to convert PDF pages to images
  - Process each slide through vision pipeline
  - Maintain slide order in document

- [ ] **Unified Media Processor**: Combine multiple inputs
  - Accept audio + multiple images + PDF slides
  - Create "session" concept to group related media
  - Unified enrichment across all media types

- [ ] **OpenSERP Integration**: Web image search for enrichment
  - Search for relevant images based on section content
  - LLM selects best images from search results
  - Download and embed in document

### Medium Term
- [ ] **Two-Phase Interactive Pipeline** (Future Enhancement)
  - Phase 1: Transcription + segmentation into categories
  - User reviews categories and rates comprehension per-category
  - Phase 2: Per-category enrichment based on individual ratings
  - Option to discuss points of misunderstanding

- [ ] **Quality Tiers**: Different container sizes for different VRAM
  - RTX 4090 (24GB): Current - Qwen2.5-7B-AWQ
  - RTX 3090 (24GB): Same as 4090
  - RTX 3060 (12GB): Smaller model (Qwen2.5-3B or quantized)
  - CPU-only: Transcription only, remote LLM

- [ ] **GitHub Auto-Commit**: Auto-commit generated markdown to repo
  - Already implemented in `server/github_ops.py`
  - Needs integration with worker output

### Long Term
- [ ] **Multi-language Support**: Better handling of non-English content
- [ ] **Speaker Diarization**: Identify different speakers
- [ ] **Video Processing**: Extract audio from video files
- [ ] **Real-time Processing**: Stream processing for live events

## 🐛 Known Issues / Limitations

1. **Image Search**: OpenSERP integration is optional (fails gracefully if service unavailable)
2. **Model Download**: First run downloads ~5GB model (cached in volume)
3. **Memory**: Requires 24GB VRAM for current model (can be optimized for smaller GPUs)
4. **JSON Parsing**: LLM responses sometimes need cleanup (handled with fallbacks)

## 📝 Notes

- **Understanding Level 0**: New feature - complete novice mode with extensive explanations
- **Image Processing**: Currently processes uploaded images; web search is fallback
- **Container**: Fully self-contained - no external dependencies required
- **Testing**: Tested with OCP conference recordings (m4a files)

## 🔗 Related Files

- `worker/Dockerfile` - Container definition
- `worker/docker/entrypoint.sh` - Startup script (vLLM + worker)
- `worker/requirements.txt` - Python dependencies
- `worker/test_transcribe.py` - Standalone transcription test script

---

**Last Updated**: 2026-01-15  
**Status**: Core pipeline complete, image processing integrated, ready for testing

