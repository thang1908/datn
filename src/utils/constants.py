from typing import Any, Dict, List

DEFAULT_CASE_TYPE = "Hỗ trợ phần mềm"


CRITERION_ORDER: List[str] = [
    "communication",
    "attitude",
    "data_collection",
    "problem_solving",
]

RUBRIC: Dict[str, Any] = {
    "communication": {
        "max_score": 10,
        "weight": 0.2,
        "violations": {
            "GT_01": {"description": "Chào đầu chưa rõ ràng hoặc chưa đúng mẫu câu chuẩn.", "deduction": 1},
            "GT_02": {"description": "Kết thúc chưa rõ ràng hoặc chưa đúng mẫu câu chuẩn.", "deduction": 1},
            "GT_03": {"description": "Xưng hô không có chủ ngữ.", "deduction": 1},
            "GT_04": {"description": "Để khoảng lặng trong giao tiếp mà không xin phép KH.", "deduction": 1},
            "GT_05": {"description": "Để KH gọi/trao đổi mà không đáp, KH phải gọi/nói lần 2 mới đáp.", "deduction": 1},
            "GT_06": {"description": "Không xin phép khách trước khi giữ/đợi để kiểm tra thông tin.", "deduction": 1},
            "GT_07": {"description": "Để KH chat nhiều (>=2 tin nhắn) mà không phản hồi (quá 2 phút).", "deduction": 1},
            "GT_08": {"description": "Yêu cầu KH chờ nhưng không cảm ơn sau khi khách chờ.", "deduction": 1},
            "GT_09": {"description": "Ngôn từ giao tiếp không lịch sự/cộc lốc/không phù hợp.", "deduction": 1},
            "GT_10": {"description": "Diễn đạt lan man/không đúng trọng tâm/chưa rõ ý, gây khó hiểu.", "deduction": 1},
            "GT_11": {"description": "Dùng thuật ngữ/tiếng đệm/tiếng lóng/từ địa phương làm KH khó hiểu.", "deduction": 1},
            "GT_12": {"description": "Không tư vấn đủ 2 tính năng theo MP AI.", "deduction": 1},
        },
    },
    "attitude": {
        "max_score": 10,
        "weight": 0.3,
        "violations": {
            "TD_01": {"description": "Thái độ thờ ơ/hời hợt; thiếu nhiệt tình; không trả lời đúng trọng tâm khiến KH lặp lại nhiều lần; dùng ngôn từ thờ ơ.", "deduction": 1},
            "TD_02": {"description": "Trả lời cho xong, không hỏi lại để xác minh thông tin.", "deduction": 1},
            "TD_03": {"description": "Ngắt lời khi KH đang trao đổi, không chú ý nội dung KH nói.", "deduction": 1},
            "TD_04": {"description": "Giao tiếp kém/không linh hoạt làm KH phản ứng gay gắt; thái độ cứng nhắc.", "deduction": 1},
            "TD_05": {"description": "Chưa chủ động xin lỗi, trấn an khi KH gặp sự cố/sai sót.", "deduction": 1},
            "TD_06": {"description": "Dùng từ/câu cộc lốc, thể hiện gắt gỏng.", "deduction": 2},
            "TD_07": {"description": "Đổ lỗi cho khách hàng.", "deduction": 2},
            "TD_08": {"description": "Tranh cãi/cãi tay đôi với KH; phản hồi đổ trách nhiệm; lớn tiếng.", "deduction": 10},
            "TD_09": {"description": "Thái độ coi thường, thách thức KH.", "deduction": 10},
            "TD_10": {"description": "Ngôn từ thô tục/không phù hợp thuần phong mỹ tục.", "deduction": 10},
            "TD_11": {"description": "Cố tình thực hiện sai yêu cầu của KH và không phản hồi lại.", "deduction": 10},
            "TD_12": {"description": "CS yêu cầu KH gọi lại.", "deduction": 1},
        },
    },
    "data_collection": {
        "max_score": 10,
        "weight": 0.1,
        "violations": {
            "TTDL_01": {"description": "Khai thác/xác nhận thiếu thông tin quan trọng.", "deduction": 5},
            "TTDL_02": {"description": "Không hỏi lại thông tin KH cần hỗ trợ; hỏi không liên quan vấn đề.", "deduction": 5},
            "TTDL_03": {"description": "Khai thác thừa thông tin đã có/có thể kiểm tra/không cần thiết.", "deduction": 5},
        },
    },
    "problem_solving": {
        "max_score": 10,
        "weight": 0.4,
        "violations": {
            "GQVD_01": {"description": "KH phản hồi: chưa được, anh không làm được, chưa đúng yêu cầu của anh.", "deduction": 10},
            "GQVD_02": {"description": "CS không đưa ra được nguyên nhân, lý do.", "deduction": 10},
            "GQVD_03": {"description": "CS phản hồi: em không xử lý được, em không biết, vẫn gay gắt.", "deduction": 10},
            "GQVD_04": {"description": "CS không thông báo chưa có tính năng.", "deduction": 10},
            "GQVD_05": {"description": "CS không ghi nhận yêu cầu.", "deduction": 10},
            "GQVD_06": {"description": "CS không hứa chuyển/ghi nhận cho bộ phận phát triển sản phẩm.", "deduction": 10},
            "GQVD_07": {"description": "CS không khai thác đủ tình trạng lỗi (tối thiểu: điều kiện xảy ra, thao tác, biểu hiện).", "deduction": 10},
            "GQVD_08": {"description": "CS không ghi nhận bug + điều hướng xử lý tiếp theo (giữ ultra/follow-up/giải pháp tạm).", "deduction": 10},
            "GQVD_09": {"description": "CS không phản hồi: xin lỗi KH, thừa nhận lỗi, không đổ lỗi.", "deduction": 10},
            "GQVD_10": {"description": "CS không hỏi làm rõ thông tin vấn đề của khách.", "deduction": 10},
        },
    },
}

NEGATIVE_REASON_MAP: Dict[str, str] = {
    "C1": "Kết thúc hội thoại nhưng KH vẫn bức xúc",
    "C2": "KH gay gắt/mất kiểm soát/lặp phàn nàn nhiều lần",
    "C3": "Đe dọa khiếu nại/phản ánh cấp cao/đăng MXH",
    "C4": "Đòi hủy hợp đồng/ngừng dùng",
    "C5": "Yêu cầu gặp quản lý/lãnh đạo",
    "C6": "Cắt lời/không cho giải thích (dựa trên ngôn từ)",
    "C7": "So sánh tiêu cực với đối thủ",
    "C8": "Đòi xử lý ngay, không chấp nhận quy trình",
    "C9": "Mất niềm tin hoàn toàn",
    "A1": "Từ chối hỗ trợ không đúng quy định (không đưa phương án)",
    "A2": "Đổ lỗi cho KH/bộ phận khác",
    "A3": "Ngôn từ chưa chuẩn mực, xúc phạm KH",
    "A4": "Tranh cãi với KH",
}