# Báo cáo tiến độ thực hiện đồ án tốt nghiệp

**Đề tài:** Hệ thống thông minh hỗ trợ học tiếng Nhật  
**Thời điểm báo cáo:** 06/2026  
**Sinh viên thực hiện:** Họ tên sinh viên  
**Giảng viên hướng dẫn:** Họ tên giảng viên hướng dẫn  

## 1. Thông tin chung về đề tài

Đề tài đồ án tốt nghiệp của em có tên là “Xây dựng hệ thống học ngoại ngữ thông minh hỗ trợ bởi AI Agent và kiến trúc GraphRAG”. Đây là một hệ thống web hướng tới việc hỗ trợ người học tiếng Nhật trong các hoạt động học tập thường gặp như tra cứu từ vựng, kanji, ngữ pháp, quản lý flashcard, ôn tập theo lịch lặp lại ngắt quãng, luyện hội thoại với AI Tutor, dịch thuật có xét đến ngữ cảnh và ôn tập lỗi thông qua các bài tập hoặc câu chuyện được AI tạo tự động.
Lý do lựa chọn đề tài xuất phát từ thực tế quá trình tự học tiếng Nhật thường bị phân tán giữa nhiều công cụ khác nhau. Người học có thể dùng một ứng dụng để tra từ điển, một ứng dụng khác để tạo flashcard, một website riêng để học ngữ pháp, một công cụ dịch để đọc tài liệu và một nền tảng khác để luyện giao tiếp. Sự rời rạc này khiến dữ liệu học tập không được kết nối thành một vòng học thống nhất. Ví dụ, một từ vựng vừa tra cứu không tự động trở thành nội dung ôn tập; lỗi sai trong hội thoại không được dùng lại để sinh bài luyện tập; cấp độ JLPT hoặc lịch sử học của người dùng chưa được khai thác đầy đủ để cá nhân hóa nội dung học.
Từ vấn đề trên, đề tài hướng tới xây dựng một nền tảng tích hợp, trong đó các chức năng tra cứu, ghi nhớ, ôn tập, luyện giao tiếp và dịch thuật được kết nối trong cùng một hệ thống. Hệ thống không chỉ cung cấp các chức năng quản lý dữ liệu học tập thông thường, mà còn tích hợp các thành phần trí tuệ nhân tạo để hỗ trợ sinh nội dung ôn tập, phản hồi hội thoại và xử lý dịch thuật theo ngữ cảnh.
Về mặt kỹ thuật, hệ thống được xây dựng theo kiến trúc nhiều tầng. Tầng giao diện người dùng sử dụng Vue 3, Vite, Tailwind CSS và Pinia. Tầng backend sử dụng Java, Spring Boot, Spring Security, JWT và JPA để xử lý xác thực, nghiệp vụ và cung cấp API REST. Dữ liệu quan hệ được lưu trữ trong PostgreSQL. Tầng AI được xây dựng bằng Python, FastAPI, LangGraph và các pipeline xử lý ngôn ngữ, đồng thời sử dụng Neo4j để lưu trữ đồ thị tri thức phục vụ bài toán dịch thuật chuyên ngành và xếp hạng nghĩa theo ngữ cảnh.


## 2. Mục tiêu của đề tài

Mục tiêu tổng quát của đề tài là thiết kế và xây dựng một hệ thống học tiếng Nhật thông minh, có khả năng hỗ trợ người học trong nhiều giai đoạn của quá trình học: từ tra cứu kiến thức, lưu trữ nội dung cần ghi nhớ, ôn tập theo lịch, luyện sử dụng trong ngữ cảnh, đến nhận phản hồi và tiếp tục cải thiện.

Các mục tiêu cụ thể của đề tài bao gồm:

- Xây dựng hệ thống web có giao diện thân thiện, cho phép người dùng đăng ký, đăng nhập, quản lý hồ sơ học tập và sử dụng các chức năng học tiếng Nhật trên trình duyệt.
- Xây dựng chức năng tra cứu từ vựng, kanji và ngữ pháp, hỗ trợ hiển thị thông tin chi tiết, ví dụ sử dụng và các quan hệ liên quan.
- Xây dựng chức năng quản lý flashcard, cho phép người học tạo bộ thẻ, thêm thẻ, chỉnh sửa thẻ và học lại các thẻ đã lưu.
- Tích hợp thuật toán lặp lại ngắt quãng SM-2 để tự động tính toán lịch ôn tập dựa trên mức độ ghi nhớ của người học.
- Xây dựng chức năng ôn tập thông minh, trong đó hệ thống có thể sinh trắc nghiệm hoặc câu chuyện tương tác dựa trên bộ thẻ, cấp độ JLPT và lỗi sai gần đây.
- Xây dựng AI Tutor hỗ trợ luyện hội thoại bằng văn bản hoặc giọng nói, có khả năng phản hồi, sửa lỗi và tổng hợp kết quả phiên học.
- Xây dựng chức năng dịch thuật, bao gồm dịch nhanh và dịch phân tích sâu theo hướng kết hợp mô hình ngôn ngữ lớn với dữ liệu ngữ nghĩa trong Neo4j.
- Thiết kế kiến trúc hệ thống đủ rõ ràng để có thể mở rộng trong tương lai, đặc biệt ở các hướng cá nhân hóa nội dung học, cải thiện chất lượng dữ liệu và triển khai thực tế.

Ngoài các mục tiêu về sản phẩm, đề tài còn có mục tiêu học thuật là vận dụng kiến thức về phát triển phần mềm, thiết kế cơ sở dữ liệu, bảo mật ứng dụng web, xây dựng REST API, phát triển frontend, tích hợp trí tuệ nhân tạo và tổ chức báo cáo đồ án tốt nghiệp theo quy chuẩn.

## 3. Nội dung công việc đã thực hiện

Tính đến thời điểm hiện tại, các chức năng lõi của hệ thống đã được hoàn thành ở mức nguyên mẫu có thể sử dụng và kiểm thử. Các thành phần chính gồm frontend, backend, cơ sở dữ liệu quan hệ, AI layer và pipeline dữ liệu đã được xây dựng và tích hợp với nhau.

### 3.1 Backend và API nghiệp vụ

Phần backend đã được xây dựng bằng Spring Boot theo mô hình phân tầng gồm Controller, Service, Repository, Entity và DTO. Hệ thống đã có các nhóm API chính cho xác thực người dùng, quản lý hồ sơ, tra cứu từ điển, bình luận, quản lý bộ thẻ flashcard, ôn tập, AI Tutor, review thông minh và dịch thuật.

Các chức năng xác thực cơ bản như đăng ký, đăng nhập, làm mới token và bảo vệ API bằng JWT đã được triển khai. Backend cũng đã có cơ chế phân quyền giữa người dùng thông thường và quản trị viên. Các dữ liệu chính như tài khoản, hồ sơ người dùng, mục từ điển, ví dụ, flashcard, bộ thẻ, thông tin SRS, phiên hội thoại và kết quả học tập được ánh xạ thành các entity và lưu trữ trong PostgreSQL.

Đối với phần flashcard, backend đã tách dữ liệu nội dung thẻ học khỏi thông tin ôn tập SRS. Điều này giúp hệ thống quản lý rõ ràng giữa nội dung người học cần ghi nhớ và trạng thái ghi nhớ của từng thẻ. Thuật toán SM-2 đã được tích hợp để cập nhật các thông số như số lần lặp lại, hệ số dễ nhớ, khoảng cách ngày và thời điểm ôn tập tiếp theo sau mỗi lần người học đánh giá kết quả ôn tập.

### 3.2 Frontend và trải nghiệm người dùng

Phần frontend đã được xây dựng bằng Vue 3, Vite, Tailwind CSS và Pinia. Hệ thống đã có các màn hình chính phục vụ luồng học tập của người dùng, bao gồm đăng nhập, đăng ký, dashboard, tra cứu từ điển, xem kanji/ngữ pháp, quản lý flashcard, phiên học flashcard, cấu hình bài ôn tập, làm quiz, đọc câu chuyện tương tác, cấu hình AI Tutor, trò chuyện với AI Tutor và xem kết quả phiên học.

Các service frontend đã được tổ chức để giao tiếp với backend thông qua Axios. Cơ chế lưu token và tự động làm mới token đã được tích hợp để giúp phiên đăng nhập ổn định hơn. Giao diện cũng đã hoàn thiện ở mức đủ để demo các chức năng chính và thể hiện được luồng học tập từ tra cứu, lưu thẻ, ôn tập đến luyện tập với AI.

Đối với chức năng học flashcard, giao diện đã hỗ trợ xem thẻ, lật thẻ và chọn mức độ ghi nhớ. Các nút đánh giá được liên kết với thuật toán SM-2 ở backend để cập nhật lịch ôn tập. Đối với phần review thông minh, frontend đã có màn hình cấu hình sinh bài và hiển thị nội dung quiz hoặc story do AI tạo ra.

### 3.3 Cơ sở dữ liệu và dữ liệu từ điển

Hệ thống sử dụng PostgreSQL để lưu trữ dữ liệu quan hệ. Các bảng chính đã được thiết kế phục vụ các nhóm nghiệp vụ như người dùng, hồ sơ học tập, từ điển, ví dụ, quan hệ mục từ, bình luận, bộ thẻ, flashcard, thông tin SRS, phiên hội thoại và kết quả học tập. Cấu trúc dữ liệu hiện tại đáp ứng được các chức năng lõi của hệ thống.

Bên cạnh PostgreSQL, hệ thống còn sử dụng Neo4j để lưu trữ dữ liệu dạng đồ thị phục vụ bài toán dịch thuật chuyên ngành. Dữ liệu trong Neo4j được tổ chức xoay quanh các thực thể như từ vựng, nghĩa và miền tri thức. Cách biểu diễn này giúp hệ thống có thể truy xuất các ứng viên nghĩa, xếp hạng nghĩa theo ngữ cảnh và cung cấp thông tin hỗ trợ cho mô hình ngôn ngữ lớn khi sinh kết quả dịch.

Các script xử lý dữ liệu đã được xây dựng để chuẩn bị dữ liệu từ các nguồn từ điển, chuyển đổi dữ liệu, sinh quan hệ và nạp dữ liệu vào PostgreSQL hoặc Neo4j. Đây là phần quan trọng vì chất lượng dữ liệu ảnh hưởng trực tiếp đến khả năng tra cứu, dịch thuật và gợi ý nội dung học.

### 3.4 AI Review, AI Tutor và dịch thuật

Phần AI layer đã được triển khai bằng Python, FastAPI và LangGraph. Hệ thống đã có pipeline phục vụ sinh bài ôn tập dưới dạng trắc nghiệm và câu chuyện tương tác. Pipeline này nhận đầu vào từ backend, bao gồm thông tin bộ thẻ, cấp độ JLPT và lỗi sai gần đây của người học, sau đó gọi mô hình ngôn ngữ lớn để sinh nội dung có cấu trúc cho frontend hiển thị.

AI Tutor đã được triển khai theo hướng hỗ trợ hội thoại bằng văn bản và giọng nói. Người học có thể tạo phiên luyện tập với chủ đề, cấp độ và từ vựng mục tiêu. Hệ thống có khả năng xử lý tin nhắn của người học, sinh phản hồi phù hợp, phát hiện lỗi và tổng hợp kết quả phiên học. Phần giọng nói đã có hướng tích hợp STT để chuyển âm thanh thành văn bản và TTS để sinh phản hồi âm thanh.

Đối với chức năng dịch thuật, hệ thống đã xây dựng pipeline kết hợp xử lý tiếng Nhật, truy vấn Neo4j và mô hình ngôn ngữ lớn. Pipeline này hướng tới việc cải thiện khả năng lựa chọn nghĩa đúng trong ngữ cảnh, đặc biệt với các từ hoặc cụm từ có nhiều nghĩa. Đây là một trong các điểm khác biệt của đề tài so với các hệ thống học tập chỉ dừng lại ở tra cứu và flashcard thông thường.

## 4. Mức độ hoàn thành hiện tại

Hiện tại, đề tài đã hoàn thành phần lớn các chức năng cốt lõi. Các module chính của hệ thống đã được xây dựng và có thể kết nối với nhau trong một luồng sử dụng tương đối hoàn chỉnh. Người dùng có thể đăng nhập, tra cứu nội dung tiếng Nhật, tạo và học flashcard, ôn tập theo thuật toán SM-2, sử dụng các bài ôn tập do AI sinh ra, luyện hội thoại với AI Tutor và sử dụng chức năng dịch thuật.

Trạng thái hiện tại có thể tóm tắt như sau:

| Hạng mục | Tình trạng |
|---|---|
| Xác thực và quản lý người dùng | Đã hoàn thành chức năng cơ bản |
| Tra cứu từ vựng, kanji, ngữ pháp | Đã hoàn thành chức năng lõi |
| Bình luận tại mục từ điển | Đã triển khai |
| Quản lý flashcard và bộ thẻ | Đã hoàn thành chức năng lõi |
| Ôn tập theo thuật toán SM-2 | Đã tích hợp và đang tiếp tục kiểm tra lỗi |
| Sinh quiz/story bằng AI | Đã triển khai pipeline và giao diện sử dụng |
| AI Tutor văn bản/giọng nói | Đã triển khai core, tiếp tục hoàn thiện trải nghiệm và xử lý lỗi |
| Dịch thuật chuyên ngành GraphRAG | Đã triển khai pipeline, tiếp tục tinh chỉnh chất lượng kết quả |
| Giao diện frontend | Đã có các màn hình chính, đang hoàn thiện chi tiết |
| Báo cáo luận văn | Đã viết bộ khung, đang đọc lại, chỉnh sửa và bổ sung hình vẽ |

Nhìn chung, sản phẩm đã vượt qua giai đoạn xây dựng nền tảng ban đầu và đang chuyển sang giai đoạn hoàn thiện. Công việc hiện tại tập trung vào sửa lỗi, kiểm thử các luồng chính, làm mượt giao diện, chuẩn hóa dữ liệu trả về giữa các tầng, bổ sung các trường hợp ngoại lệ và chuẩn bị nội dung báo cáo.

## 5. Công việc đang thực hiện

Trong giai đoạn hiện tại, trọng tâm công việc không còn là xây dựng mới toàn bộ chức năng, mà là hoàn thiện các chức năng đã có để hệ thống ổn định hơn và phù hợp hơn cho việc demo, đánh giá đồ án.

Các công việc kỹ thuật đang được thực hiện gồm:

- Rà soát các luồng nghiệp vụ chính từ frontend đến backend và AI layer.
- Sửa các lỗi phát sinh khi gọi API, đặc biệt ở các luồng có nhiều thành phần liên quan như AI Tutor, Review Quiz/Story và dịch thuật.
- Kiểm tra lại thuật toán SM-2, truy vấn danh sách thẻ đến hạn và hiển thị trạng thái ôn tập trên giao diện.
- Chuẩn hóa dữ liệu request/response giữa frontend, backend và AI layer.
- Cải thiện xử lý lỗi khi mô hình ngôn ngữ lớn trả về dữ liệu không đúng cấu trúc hoặc khi dịch vụ AI tạm thời không phản hồi.
- Hoàn thiện giao diện ở các màn hình chính để phục vụ báo cáo và demo.
- Kiểm tra lại dữ liệu từ điển, dữ liệu Neo4j và các script seed dữ liệu.
- Bổ sung test cho một số luồng quan trọng, ưu tiên các phần có rủi ro lỗi cao.

Ngoài công việc kỹ thuật, phần tài liệu hệ thống cũng đang được cập nhật. Các tài liệu thiết kế, mô tả schema, mô tả pipeline AI, hợp đồng API và phần tổng quan kiến trúc đã được viết ở mức cơ bản. Những tài liệu này sẽ được dùng làm cơ sở để hoàn thiện các chương trong luận văn.

## 6. Tiến độ viết báo cáo luận văn

Về phần báo cáo luận văn, hiện tại đã viết được bộ khung chính. Nội dung đã bao gồm các phần mở đầu như lời cam kết, lời cảm ơn, tóm tắt tiếng Việt, abstract tiếng Anh, danh mục từ viết tắt và chương giới thiệu đề tài. Các chương tiếp theo cũng đã được định hướng theo cấu trúc: khảo sát và phân tích yêu cầu, công nghệ sử dụng, thiết kế và phát triển hệ thống, các giải pháp nổi bật, kết luận và hướng phát triển.

Phần đã hoàn thành ở mức sơ bộ gồm:

- Xác định tên đề tài, bối cảnh và lý do chọn đề tài.
- Viết phần mục tiêu, phạm vi và định hướng giải pháp.
- Mô tả tổng quan các nhóm chức năng của hệ thống.
- Phác thảo kiến trúc tổng thể của hệ thống.
- Liệt kê các công nghệ chính được sử dụng.
- Tổng hợp các chức năng đã triển khai trong frontend, backend, database và AI layer.
- Chuẩn bị một số tài liệu kỹ thuật phụ trợ để đưa vào nội dung luận văn.

Phần đang tiếp tục thực hiện gồm:

- Đọc lại toàn bộ nội dung đã viết để chỉnh sửa văn phong, tránh lặp ý và đảm bảo tính học thuật.
- Bổ sung mô tả chi tiết hơn cho các chương về thiết kế hệ thống, cơ sở dữ liệu và AI pipeline.
- Bổ sung hình vẽ kiến trúc tổng thể, sơ đồ use case, sơ đồ luồng xử lý, sơ đồ cơ sở dữ liệu và hình minh họa giao diện.
- Chuẩn hóa thuật ngữ giữa báo cáo, mã nguồn và tài liệu kỹ thuật.
- Bổ sung phần đánh giá kết quả, hạn chế còn tồn tại và hướng phát triển.
- Kiểm tra định dạng theo mẫu luận văn của nhà trường.
- Chuyển nội dung báo cáo từ Markdown sang LaTeX để thuận tiện cho việc dàn trang, quản lý hình vẽ, bảng biểu, tài liệu tham khảo và xuất bản PDF theo đúng mẫu luận văn.

Dự kiến trong thời gian tới, phần viết luận văn sẽ tập trung vào việc biến bộ khung hiện tại thành bản báo cáo hoàn chỉnh. Các hình vẽ sẽ được bổ sung để giúp người đọc dễ hình dung kiến trúc hệ thống và các luồng xử lý quan trọng. Đồng thời, nội dung mô tả chức năng sẽ được đối chiếu lại với sản phẩm thực tế để đảm bảo báo cáo phản ánh đúng trạng thái triển khai.

## 7. Kế hoạch công việc tiếp theo

Trong giai đoạn tiếp theo, công việc sẽ được chia thành hai hướng song song: hoàn thiện sản phẩm và hoàn thiện luận văn.

Đối với sản phẩm, các công việc ưu tiên gồm kiểm thử toàn bộ luồng sử dụng chính, sửa lỗi còn tồn tại, hoàn thiện giao diện demo và đảm bảo các chức năng cốt lõi hoạt động ổn định. Các luồng cần được kiểm tra kỹ bao gồm đăng nhập, tra cứu từ điển, thêm flashcard, ôn tập theo SM-2, sinh bài quiz/story, luyện hội thoại với AI Tutor và dịch thuật chuyên ngành. Bên cạnh đó, cần chuẩn bị dữ liệu mẫu phù hợp để buổi demo thể hiện rõ giá trị của hệ thống.

Đối với luận văn, các công việc ưu tiên gồm hoàn thiện các chương nội dung, bổ sung hình vẽ, rà soát văn phong và chuẩn hóa định dạng. Phần thiết kế hệ thống cần được trình bày rõ theo từng tầng: frontend, backend, cơ sở dữ liệu và AI layer. Phần giải pháp nổi bật cần tập trung vào các điểm có tính đóng góp của đề tài như SM-2, AI Review Pipeline, AI Tutor đa phương thức và Neo4j GraphRAG cho dịch thuật.

Kế hoạch ngắn hạn có thể tóm tắt như sau:

| Công việc | Mục tiêu |
|---|---|
| Rà soát và sửa lỗi chức năng | Đảm bảo hệ thống chạy ổn định cho các luồng demo chính |
| Hoàn thiện giao diện | Cải thiện trải nghiệm người dùng và hình ảnh minh họa trong báo cáo |
| Bổ sung test | Giảm rủi ro lỗi ở các chức năng quan trọng |
| Chuẩn bị dữ liệu demo | Có dữ liệu đủ tốt để trình bày các tính năng |
| Hoàn thiện nội dung luận văn | Chuyển bộ khung hiện tại thành bản báo cáo đầy đủ |
| Bổ sung hình vẽ | Minh họa kiến trúc, cơ sở dữ liệu, use case và luồng xử lý |
| Chuyển luận văn sang LaTeX | Dàn trang báo cáo, quản lý hình vẽ/bảng biểu/tài liệu tham khảo và xuất PDF theo mẫu |
| Kiểm tra định dạng | Đảm bảo phù hợp với mẫu luận văn |

## 8. Kết luận

Tính đến thời điểm báo cáo, đồ án đã hoàn thành các chức năng lõi và bước đầu hình thành một hệ thống học tiếng Nhật thông minh có khả năng sử dụng thực tế ở mức nguyên mẫu. Các thành phần chính gồm frontend, backend, PostgreSQL, AI layer và Neo4j đã được xây dựng và tích hợp. Hệ thống đã hỗ trợ các chức năng quan trọng như tra cứu, quản lý flashcard, ôn tập theo SM-2, sinh bài ôn tập bằng AI, luyện hội thoại với AI Tutor và dịch thuật theo ngữ cảnh.

Công việc hiện tại tập trung vào sửa lỗi, hoàn thiện chi tiết, kiểm thử các luồng chính và chuẩn bị dữ liệu demo. Về phần luận văn, bộ khung báo cáo đã được xây dựng, hiện đang trong quá trình đọc lại, chỉnh sửa, hoàn thiện nội dung và bổ sung hình vẽ. Trong thời gian tới, mục tiêu chính là ổn định sản phẩm, hoàn thiện báo cáo và chuẩn bị tốt cho quá trình bảo vệ đồ án tốt nghiệp.
