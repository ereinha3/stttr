# Whispr TODO / Roadmap

## ✅ Completed

### Core Infrastructure
- [x] Self-contained Docker container with CUDA support
- [x] GPU-accelerated Whisper transcription (large-v3)
- [x] vLLM integration with Qwen2.5-7B-Instruct-AWQ
- [x] FastAPI worker service with `/process` endpoint
- [x] Understanding level system (0-5) with adaptive depth
- [x] Tesseract OCR integration
- [x] Image analysis pipeline (OCR + LLM)
- [x] Image-to-section placement logic
- [x] Markdown generation with embedded images
- [x] Standalone transcription test script

### Features
- [x] Audio transcription with language detection
- [x] LLM summarization with sections, glossary, Q&A
- [x] Image upload support in API
- [x] Image analysis (description, keywords, classification)
- [x] Intelligent image placement in document sections
- [x] Understanding level 0 (complete novice) support

## 🔄 In Progress

- [ ] Testing image processing with real conference photos
- [ ] Verifying image placement accuracy

## 📋 Next Steps (Immediate)

### Testing & Validation
- [ ] Test image processing with OCP conference photos (`media/ocp/credo/*.jpeg`)
- [ ] Verify image placement logic matches images to correct sections
- [ ] Test understanding_level=0 (complete novice) output depth
- [ ] Validate markdown output formatting with embedded images

### Enhancements
- [ ] Improve markdown image formatting (alt text, captions, sizing)
- [ ] Add image confidence scores to output metadata
- [ ] Better error handling for image processing failures
- [ ] Add image metadata to final JSON response

## 🎯 Short Term Goals

### PDF/Slideshow Processing
- [ ] Implement PDF page extraction (`pdf2image`)
- [ ] Process PDF slides through vision pipeline
- [ ] Maintain slide order in document
- [ ] Support PPTX files (convert to images first)
- [ ] Extract slide text and match to sections

### Unified Media Processor
- [ ] Create "session" concept to group related media
- [ ] Accept audio + images + PDF slides in single request
- [ ] Unified enrichment across all media types
- [ ] Cross-reference content between media types
- [ ] Generate comprehensive report from all inputs

### OpenSERP Integration
- [ ] Set up OpenSERP service or find alternative
- [ ] Implement web image search based on section content
- [ ] LLM-based image selection from search results
- [ ] Download and embed selected images
- [ ] Fallback gracefully if service unavailable

## 🚀 Medium Term Goals

### Quality Tiers / Container Variants
- [ ] Create RTX 4090/3090 variant (24GB) - Current
- [ ] Create RTX 3060 variant (12GB) - Smaller model
- [ ] Create CPU-only variant - Transcription + remote LLM
- [ ] Auto-detect GPU and select appropriate model
- [ ] Document VRAM requirements per tier

### Two-Phase Interactive Pipeline (Future)
- [ ] Phase 1: Transcription + automatic segmentation
- [ ] User interface for category review
- [ ] Per-category comprehension rating
- [ ] Phase 2: Per-category enrichment
- [ ] Discussion/feedback mechanism for misunderstandings
- [ ] Iterative refinement based on user input

### GitHub Integration
- [ ] Wire up `server/github_ops.py` with worker output
- [ ] Auto-commit generated markdown files
- [ ] Organize by date/topic in repo structure
- [ ] Commit messages with metadata

## 🔮 Long Term Vision

### Advanced Features
- [ ] Multi-language support (better handling of non-English)
- [ ] Speaker diarization (identify different speakers)
- [ ] Video processing (extract audio from video)
- [ ] Real-time processing (stream processing for live events)
- [ ] Batch processing (multiple files in one request)

### Performance
- [ ] Optimize model loading time
- [ ] Implement request queuing
- [ ] Add caching for repeated content
- [ ] Parallel image processing
- [ ] Streaming transcription for long files

### User Experience
- [ ] Web UI for file upload and review
- [ ] Progress indicators for long-running jobs
- [ ] Preview mode before final generation
- [ ] Edit/refine generated content
- [ ] Export to multiple formats (PDF, HTML, etc.)

## 🐛 Known Issues / Technical Debt

- [ ] Image search (OpenSERP) fails gracefully but could be more robust
- [ ] LLM JSON parsing sometimes needs cleanup (has fallbacks)
- [ ] Model download on first run takes time (could pre-bake)
- [ ] Memory usage could be optimized for smaller GPUs
- [ ] Error messages could be more user-friendly
- [ ] Logging could be more structured

## 📝 Notes

- **Understanding Level 0**: Newly implemented - complete novice mode
- **Image Processing**: Currently works with uploaded images; web search is optional
- **Container**: Fully self-contained - no external services required
- **Testing**: Tested with OCP conference recordings

---

**Last Updated**: 2026-01-15  
**Next Session Focus**: Test image processing, verify placement logic, enhance markdown output

