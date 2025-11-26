# Implementation Plan

- [ ] 1. Optimize Dockerfile to reduce image size
  - Combine RUN commands to reduce layer count
  - Ensure cleanup commands are in the same layer as operations that create temporary files
  - Verify --no-install-recommends is used for all apt-get install commands
  - Remove SDK archive files in the same layer where extraction happens
  - _Requirements: 2.1, 2.2, 2.3, 2.4, 5.1, 5.2, 5.4_

- [ ]* 1.1 Write property test for image size compliance
  - **Property 4: Image size compliance**
  - **Validates: Requirements 2.1**

- [ ]* 1.2 Write property test for temporary files removal
  - **Property 5: Temporary files removal**
  - **Validates: Requirements 2.2, 2.3**

- [ ] 2. Fix build-local.sh size validation logic
  - Correct the image size parsing to use bytes instead of human-readable format
  - Fix the comparison logic to properly detect images exceeding 2GB
  - Update warning and success messages to show both formats
  - _Requirements: 3.1, 3.2, 3.3, 3.4_

- [ ]* 2.1 Write property test for size parsing accuracy
  - **Property 6: Size parsing accuracy**
  - **Validates: Requirements 3.1, 3.4**

- [ ] 3. Enhance validation scripts
  - Update validate-docker-image-size.sh to use correct byte comparison
  - Enhance validate-docker-image-contents.sh to check for temporary files
  - Add specific error messages for each validation failure
  - Test validation scripts with both passing and failing images
  - _Requirements: 6.1, 6.2, 6.3, 6.4_

- [ ]* 3.1 Write property test for SDK directory presence
  - **Property 7: SDK directory presence**
  - **Validates: Requirements 6.1**

- [ ]* 3.2 Write property test for build tools availability
  - **Property 8: Build tools availability**
  - **Validates: Requirements 6.2**

- [ ]* 3.3 Write property test for builder user permissions
  - **Property 9: Builder user permissions**
  - **Validates: Requirements 6.3**

- [ ]* 3.4 Write property test for validation error reporting
  - **Property 10: Validation error reporting**
  - **Validates: Requirements 6.4**

- [ ] 4. Add Windows-specific documentation to README
  - Create a "Building on Windows" section in docker/sdk/README.md
  - Add PowerShell and CMD command examples
  - Document volume mount path formats for Windows
  - Include troubleshooting section for common Windows issues
  - Add Docker Desktop setup requirements
  - _Requirements: 4.1, 4.2, 4.3, 4.4_

- [ ] 5. Checkpoint - Verify all changes work on Windows
  - Build image locally on Windows using build-local.sh
  - Verify image size is under 2GB
  - Test volume mounting with Windows paths
  - Run validation scripts and confirm they pass
  - Ensure all tests pass, ask the user if questions arise
  - _Requirements: 1.1, 1.2, 1.4, 2.1_
